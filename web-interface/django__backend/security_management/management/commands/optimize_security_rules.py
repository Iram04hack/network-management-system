"""
Commande Django pour l'optimisation sophistiquée des règles de sécurité.

Cette commande effectue :
- L'analyse complète des conflits entre règles
- L'optimisation automatique des performances
- La consolidation des règles redondantes
- L'intégration avec les services Docker pour validation
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from ...models import SecurityRuleModel, SecurityAlertModel, AuditLogModel
from ...domain.conflict_detector_factory import conflict_detector_factory
from ...application.detect_rule_conflicts_use_case import DetectRuleConflictsUseCase
from ...domain.impact_analysis import AdvancedRuleMetricsCalculator, DockerMetricsCollector
from ...infrastructure.repositories import (
    DjangoSecurityRuleRepository, DjangoSecurityAlertRepository
)
from ...infrastructure.docker_integration import (
    SuricataDockerAdapter, Fail2BanDockerAdapter, TrafficControlDockerAdapter
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Commande d'optimisation avancée des règles de sécurité.
    
    Usage:
        python manage.py optimize_security_rules [options]
    """
    
    help = 'Optimise les règles de sécurité avec analyse de conflits et intégration Docker'
    
    def __init__(self):
        super().__init__()
        # Initialiser les services
        self.rule_repository = DjangoSecurityRuleRepository()
        self.conflict_use_case = DetectRuleConflictsUseCase(
            rule_repository=self.rule_repository,
            conflict_detector_factory=conflict_detector_factory
        )
        self.metrics_calculator = AdvancedRuleMetricsCalculator()
        self.metrics_collector = DockerMetricsCollector()
        
        # Adaptateurs Docker
        self.docker_services = {
            'suricata': SuricataDockerAdapter(),
            'fail2ban': Fail2BanDockerAdapter(),
            'traffic_control': TrafficControlDockerAdapter()
        }
        
        # Statistiques d'optimisation
        self.optimization_stats = {
            'rules_analyzed': 0,
            'conflicts_detected': 0,
            'conflicts_resolved': 0,
            'rules_optimized': 0,
            'rules_consolidated': 0,
            'performance_improved': False,
            'docker_services_validated': 0
        }
    
    def add_arguments(self, parser):
        """Ajoute les arguments de la commande."""
        parser.add_argument(
            '--rule-type',
            choices=['firewall', 'ids', 'access_control', 'all'],
            default='all',
            help='Type de règles à optimiser (default: all)'
        )
        
        parser.add_argument(
            '--auto-resolve',
            action='store_true',
            help='Résout automatiquement les conflits simples'
        )
        
        parser.add_argument(
            '--consolidate',
            action='store_true',
            help='Consolide les règles redondantes'
        )
        
        parser.add_argument(
            '--validate-docker',
            action='store_true',
            help='Valide toutes les règles via les services Docker'
        )
        
        parser.add_argument(
            '--performance-check',
            action='store_true',
            help='Effectue une analyse de performance complète'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans modifications effectives'
        )
        
        parser.add_argument(
            '--output-format',
            choices=['text', 'json'],
            default='text',
            help='Format de sortie (default: text)'
        )
        
        parser.add_argument(
            '--export-report',
            type=str,
            help='Chemin pour exporter le rapport d\'optimisation'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mode verbeux'
        )
    
    def handle(self, *args, **options):
        """Point d'entrée principal de la commande."""
        try:
            self.verbosity = options.get('verbosity', 1)
            self.verbose = options.get('verbose', False)
            
            start_time = timezone.now()
            
            if self.verbose:
                self.stdout.write(
                    self.style.SUCCESS(f'🔧 Démarrage de l\'optimisation des règles de sécurité - {start_time}')
                )
            
            # Étape 1: Analyse des règles existantes
            self._log_step("Analyse des règles existantes")
            rules_to_analyze = self._get_rules_to_analyze(options['rule_type'])
            self.optimization_stats['rules_analyzed'] = len(rules_to_analyze)
            
            if not rules_to_analyze:
                self.stdout.write(
                    self.style.WARNING('⚠️  Aucune règle trouvée pour l\'optimisation')
                )
                return
            
            # Étape 2: Détection des conflits
            self._log_step("Détection des conflits")
            conflicts = self._detect_conflicts(rules_to_analyze, options['rule_type'])
            self.optimization_stats['conflicts_detected'] = len(conflicts)
            
            # Étape 3: Validation Docker (optionnelle)
            if options['validate_docker']:
                self._log_step("Validation via services Docker")
                docker_results = self._validate_rules_via_docker(rules_to_analyze)
                self.optimization_stats['docker_services_validated'] = len(docker_results)
            
            # Étape 4: Analyse de performance (optionnelle)
            performance_analysis = None
            if options['performance_check']:
                self._log_step("Analyse de performance")
                performance_analysis = self._analyze_performance(rules_to_analyze)
                self.optimization_stats['performance_improved'] = performance_analysis.get('improvements_available', False)
            
            # Étape 5: Résolution automatique des conflits (optionnelle)
            if options['auto_resolve'] and conflicts:
                self._log_step("Résolution automatique des conflits")
                resolved_count = self._auto_resolve_conflicts(conflicts, options['dry_run'])
                self.optimization_stats['conflicts_resolved'] = resolved_count
            
            # Étape 6: Consolidation des règles (optionnelle)
            if options['consolidate']:
                self._log_step("Consolidation des règles redondantes")
                consolidated_count = self._consolidate_redundant_rules(conflicts, options['dry_run'])
                self.optimization_stats['rules_consolidated'] = consolidated_count
            
            # Étape 7: Optimisation des performances
            optimization_count = self._optimize_rule_performance(rules_to_analyze, options['dry_run'])
            self.optimization_stats['rules_optimized'] = optimization_count
            
            # Génération du rapport
            end_time = timezone.now()
            duration = end_time - start_time
            
            report = self._generate_optimization_report(
                rules_to_analyze, conflicts, performance_analysis, duration
            )
            
            # Affichage des résultats
            self._display_results(report, options['output_format'])
            
            # Export du rapport (optionnel)
            if options['export_report']:
                self._export_report(report, options['export_report'])
            
            # Audit log
            self._log_optimization_audit(options)
            
            if self.verbose:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Optimisation terminée en {duration.total_seconds():.2f}s')
                )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation des règles: {str(e)}")
            raise CommandError(f'Erreur lors de l\'optimisation: {str(e)}')
    
    def _get_rules_to_analyze(self, rule_type: str) -> List[SecurityRuleModel]:
        """Récupère les règles à analyser selon le type spécifié."""
        queryset = SecurityRuleModel.objects.filter(is_active=True)
        
        if rule_type != 'all':
            queryset = queryset.filter(rule_type=rule_type)
        
        rules = list(queryset.order_by('priority', 'created_at'))
        
        if self.verbose:
            self.stdout.write(f"📊 {len(rules)} règles trouvées pour l'analyse")
        
        return rules
    
    def _detect_conflicts(self, rules: List[SecurityRuleModel], rule_type: str) -> List:
        """Détecte les conflits entre les règles."""
        all_conflicts = []
        
        if rule_type == 'all':
            # Analyser par type de règle
            for rtype in ['firewall', 'ids', 'access_control']:
                type_rules = [r for r in rules if r.rule_type == rtype]
                if type_rules:
                    conflicts = self.conflict_use_case.analyze_ruleset_conflicts(rtype)
                    all_conflicts.extend(conflicts)
        else:
            # Analyser un type spécifique
            conflicts = self.conflict_use_case.analyze_ruleset_conflicts(rule_type)
            all_conflicts.extend(conflicts)
        
        if self.verbose:
            conflict_types = {}
            for conflict in all_conflicts:
                ctype = getattr(conflict, 'conflict_type', 'unknown')
                conflict_types[ctype] = conflict_types.get(ctype, 0) + 1
            
            self.stdout.write(f"⚠️  {len(all_conflicts)} conflits détectés:")
            for ctype, count in conflict_types.items():
                self.stdout.write(f"   - {ctype}: {count}")
        
        return all_conflicts
    
    def _validate_rules_via_docker(self, rules: List[SecurityRuleModel]) -> Dict[str, Any]:
        """Valide les règles via les services Docker."""
        validation_results = {
            'suricata': {'validated': 0, 'errors': 0},
            'fail2ban': {'validated': 0, 'errors': 0},
            'traffic_control': {'validated': 0, 'errors': 0}
        }
        
        for rule in rules:
            detector = conflict_detector_factory.get_detector(rule.rule_type)
            if not detector:
                continue
            
            try:
                # Validation spécifique selon le type
                if rule.rule_type == 'firewall' and hasattr(detector, '_validate_rule_via_docker'):
                    result = detector._validate_rule_via_docker(rule.content)
                    service = 'traffic_control'
                elif rule.rule_type == 'ids' and hasattr(detector, '_validate_rule_via_docker'):
                    result = detector._validate_rule_via_docker(rule.content)
                    service = 'suricata'
                elif rule.rule_type == 'access_control' and hasattr(detector, '_validate_rule_via_docker'):
                    result = detector._validate_rule_via_docker(rule.content)
                    service = 'fail2ban'
                else:
                    continue
                
                if result.get('valid', True):
                    validation_results[service]['validated'] += 1
                else:
                    validation_results[service]['errors'] += 1
                    if self.verbose:
                        self.stdout.write(
                            self.style.WARNING(
                                f"❌ Règle {rule.id} invalide: {result.get('error', 'Erreur inconnue')}"
                            )
                        )
                        
            except Exception as e:
                if self.verbose:
                    self.stdout.write(
                        self.style.ERROR(f"🔥 Erreur lors de la validation de la règle {rule.id}: {str(e)}")
                    )
        
        if self.verbose:
            total_validated = sum(r['validated'] for r in validation_results.values())
            total_errors = sum(r['errors'] for r in validation_results.values())
            self.stdout.write(f"✅ {total_validated} règles validées, ❌ {total_errors} erreurs")
        
        return validation_results
    
    def _analyze_performance(self, rules: List[SecurityRuleModel]) -> Dict[str, Any]:
        """Analyse les performances des règles."""
        try:
            # Collecter les métriques Docker
            current_metrics = self.metrics_collector.collect_all_metrics()
            
            performance_analysis = {
                'total_rules': len(rules),
                'performance_score': 0.0,
                'bottlenecks': [],
                'improvements_available': False,
                'recommendations': []
            }
            
            # Analyser l'impact de chaque règle
            total_impact = 0.0
            high_impact_rules = []
            
            for rule in rules:
                try:
                    impact = self.metrics_calculator.calculate_rule_impact(
                        rule_type=rule.rule_type,
                        rule_content=rule.content,
                        current_metrics=current_metrics
                    )
                    
                    # Évaluer l'impact performance
                    if hasattr(impact, 'performance_metrics'):
                        perf_metrics = impact.performance_metrics
                        rule_impact = (
                            getattr(perf_metrics, 'cpu_usage_percent', 0) * 0.4 +
                            getattr(perf_metrics, 'memory_usage_mb', 0) / 1000 * 0.3 +
                            getattr(perf_metrics, 'network_latency_ms', 0) / 1000 * 0.3
                        )
                        
                        total_impact += rule_impact
                        
                        if rule_impact > 2.0:  # Seuil d'impact élevé
                            high_impact_rules.append({
                                'rule_id': rule.id,
                                'rule_name': rule.name,
                                'impact_score': rule_impact,
                                'type': rule.rule_type
                            })
                            
                except Exception as e:
                    if self.verbose:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  Erreur analyse performance règle {rule.id}: {str(e)}")
                        )
            
            # Calculer le score global
            if rules:
                avg_impact = total_impact / len(rules)
                performance_analysis['performance_score'] = max(0.0, 10.0 - avg_impact)
                
                if avg_impact > 2.0:
                    performance_analysis['improvements_available'] = True
                    performance_analysis['recommendations'].append(
                        "Optimisation recommandée: impact performance élevé détecté"
                    )
            
            # Identifier les goulots d'étranglement
            if high_impact_rules:
                performance_analysis['bottlenecks'] = high_impact_rules[:5]  # Top 5
                performance_analysis['recommendations'].append(
                    f"{len(high_impact_rules)} règles à fort impact identifiées"
                )
            
            if self.verbose:
                self.stdout.write(
                    f"📈 Score de performance: {performance_analysis['performance_score']:.2f}/10"
                )
                if high_impact_rules:
                    self.stdout.write(f"⚠️  {len(high_impact_rules)} règles à fort impact détectées")
            
            return performance_analysis
            
        except Exception as e:
            if self.verbose:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Erreur lors de l'analyse de performance: {str(e)}")
                )
            return {'error': str(e)}
    
    def _auto_resolve_conflicts(self, conflicts: List, dry_run: bool = False) -> int:
        """Résout automatiquement les conflits simples."""
        resolved_count = 0
        
        for conflict in conflicts:
            conflict_type = getattr(conflict, 'conflict_type', '')
            
            # Résolution automatique pour les types simples
            if conflict_type == 'redundant':
                if self._resolve_redundant_conflict(conflict, dry_run):
                    resolved_count += 1
            elif conflict_type == 'generalization':
                if self._resolve_generalization_conflict(conflict, dry_run):
                    resolved_count += 1
        
        if self.verbose and resolved_count > 0:
            action = "seraient résolus" if dry_run else "résolus"
            self.stdout.write(f"🔧 {resolved_count} conflits {action} automatiquement")
        
        return resolved_count
    
    def _resolve_redundant_conflict(self, conflict, dry_run: bool = False) -> bool:
        """Résout un conflit de redondance en supprimant la règle la moins prioritaire."""
        try:
            rule1_id = getattr(conflict, 'rule1_id', None)
            rule2_id = getattr(conflict, 'rule2_id', None)
            
            if not rule1_id or not rule2_id:
                return False
            
            # Récupérer les règles
            rule1 = SecurityRuleModel.objects.filter(id=rule1_id).first()
            rule2 = SecurityRuleModel.objects.filter(id=rule2_id).first()
            
            if not rule1 or not rule2:
                return False
            
            # Déterminer quelle règle supprimer (la moins prioritaire ou la plus récente)
            if rule1.priority > rule2.priority:
                rule_to_remove = rule1
                rule_to_keep = rule2
            elif rule1.priority < rule2.priority:
                rule_to_remove = rule2
                rule_to_keep = rule1
            else:
                # Même priorité, supprimer la plus récente
                rule_to_remove = rule1 if rule1.created_at > rule2.created_at else rule2
                rule_to_keep = rule2 if rule1.created_at > rule2.created_at else rule1
            
            if not dry_run:
                # Désactiver plutôt que supprimer pour préserver l'historique
                rule_to_remove.is_active = False
                rule_to_remove.save()
                
                # Ajouter une note dans les métadonnées
                metadata = rule_to_remove.metadata or {}
                metadata['deactivated_reason'] = f'Redundant with rule {rule_to_keep.id}'
                metadata['deactivated_at'] = timezone.now().isoformat()
                rule_to_remove.metadata = metadata
                rule_to_remove.save()
            
            if self.verbose:
                action = "serait désactivée" if dry_run else "désactivée"
                self.stdout.write(
                    f"🔧 Règle redondante {rule_to_remove.id} {action} (redondante avec {rule_to_keep.id})"
                )
            
            return True
            
        except Exception as e:
            if self.verbose:
                self.stdout.write(
                    self.style.ERROR(f"❌ Erreur lors de la résolution du conflit redondant: {str(e)}")
                )
            return False
    
    def _resolve_generalization_conflict(self, conflict, dry_run: bool = False) -> bool:
        """Résout un conflit de généralisation en supprimant la règle spécifique."""
        try:
            rule1_id = getattr(conflict, 'rule1_id', None)
            rule2_id = getattr(conflict, 'rule2_id', None)
            
            if not rule1_id or not rule2_id:
                return False
            
            # Dans un conflit de généralisation, une règle est plus générale que l'autre
            # Selon la logique du détecteur, rule1 est généralement la plus générale
            rule_to_remove = SecurityRuleModel.objects.filter(id=rule2_id).first()
            rule_to_keep = SecurityRuleModel.objects.filter(id=rule1_id).first()
            
            if not rule_to_remove or not rule_to_keep:
                return False
            
            if not dry_run:
                rule_to_remove.is_active = False
                rule_to_remove.save()
                
                metadata = rule_to_remove.metadata or {}
                metadata['deactivated_reason'] = f'Generalized by rule {rule_to_keep.id}'
                metadata['deactivated_at'] = timezone.now().isoformat()
                rule_to_remove.metadata = metadata
                rule_to_remove.save()
            
            if self.verbose:
                action = "serait désactivée" if dry_run else "désactivée"
                self.stdout.write(
                    f"🔧 Règle spécifique {rule_to_remove.id} {action} (généralisée par {rule_to_keep.id})"
                )
            
            return True
            
        except Exception as e:
            if self.verbose:
                self.stdout.write(
                    self.style.ERROR(f"❌ Erreur lors de la résolution du conflit de généralisation: {str(e)}")
                )
            return False
    
    def _consolidate_redundant_rules(self, conflicts: List, dry_run: bool = False) -> int:
        """Consolide les règles redondantes identiques."""
        consolidated_count = 0
        
        # Identifier les groupes de règles redondantes
        redundant_groups = self._identify_redundant_groups(conflicts)
        
        for group in redundant_groups:
            if len(group) > 1:
                if self._consolidate_rule_group(group, dry_run):
                    consolidated_count += len(group) - 1  # -1 car on garde une règle
        
        if self.verbose and consolidated_count > 0:
            action = "seraient consolidées" if dry_run else "consolidées"
            self.stdout.write(f"📦 {consolidated_count} règles {action}")
        
        return consolidated_count
    
    def _identify_redundant_groups(self, conflicts: List) -> List[List[int]]:
        """Identifie les groupes de règles redondantes."""
        redundant_pairs = []
        
        for conflict in conflicts:
            if getattr(conflict, 'conflict_type', '') == 'redundant':
                rule1_id = getattr(conflict, 'rule1_id', None)
                rule2_id = getattr(conflict, 'rule2_id', None)
                if rule1_id and rule2_id:
                    redundant_pairs.append((rule1_id, rule2_id))
        
        # Grouper les paires en groupes connectés
        groups = []
        processed_rules = set()
        
        for rule1_id, rule2_id in redundant_pairs:
            if rule1_id in processed_rules or rule2_id in processed_rules:
                # Ajouter aux groupes existants
                for group in groups:
                    if rule1_id in group or rule2_id in group:
                        group.update([rule1_id, rule2_id])
                        processed_rules.update([rule1_id, rule2_id])
                        break
            else:
                # Créer un nouveau groupe
                new_group = {rule1_id, rule2_id}
                groups.append(new_group)
                processed_rules.update([rule1_id, rule2_id])
        
        return [list(group) for group in groups]
    
    def _consolidate_rule_group(self, rule_ids: List[int], dry_run: bool = False) -> bool:
        """Consolide un groupe de règles redondantes."""
        try:
            rules = SecurityRuleModel.objects.filter(id__in=rule_ids, is_active=True)
            if len(rules) < 2:
                return False
            
            # Choisir la règle à conserver (la plus ancienne avec la meilleure priorité)
            main_rule = min(rules, key=lambda r: (r.priority, r.created_at))
            rules_to_merge = [r for r in rules if r.id != main_rule.id]
            
            if not dry_run:
                # Mettre à jour la règle principale avec les métadonnées consolidées
                consolidated_metadata = main_rule.metadata or {}
                consolidated_metadata['consolidated_from'] = [r.id for r in rules_to_merge]
                consolidated_metadata['consolidated_at'] = timezone.now().isoformat()
                
                # Ajouter les descriptions des règles mergées
                descriptions = [main_rule.description or '']
                descriptions.extend([r.description or '' for r in rules_to_merge if r.description])
                consolidated_metadata['merged_descriptions'] = descriptions
                
                main_rule.metadata = consolidated_metadata
                main_rule.save()
                
                # Désactiver les autres règles
                for rule in rules_to_merge:
                    rule.is_active = False
                    rule_metadata = rule.metadata or {}
                    rule_metadata['consolidated_into'] = main_rule.id
                    rule_metadata['consolidated_at'] = timezone.now().isoformat()
                    rule.metadata = rule_metadata
                    rule.save()
            
            if self.verbose:
                action = "seraient consolidées" if dry_run else "consolidées"
                rule_ids_str = ', '.join(str(r.id) for r in rules_to_merge)
                self.stdout.write(
                    f"📦 Règles {rule_ids_str} {action} dans la règle {main_rule.id}"
                )
            
            return True
            
        except Exception as e:
            if self.verbose:
                self.stdout.write(
                    self.style.ERROR(f"❌ Erreur lors de la consolidation: {str(e)}")
                )
            return False
    
    def _optimize_rule_performance(self, rules: List[SecurityRuleModel], dry_run: bool = False) -> int:
        """Optimise les performances des règles."""
        optimized_count = 0
        
        for rule in rules:
            # Optimisations basiques selon le type de règle
            optimizations = self._identify_rule_optimizations(rule)
            
            if optimizations and not dry_run:
                # Appliquer les optimisations
                if self._apply_rule_optimizations(rule, optimizations):
                    optimized_count += 1
            elif optimizations:
                optimized_count += 1
        
        if self.verbose and optimized_count > 0:
            action = "seraient optimisées" if dry_run else "optimisées"
            self.stdout.write(f"⚡ {optimized_count} règles {action} pour les performances")
        
        return optimized_count
    
    def _identify_rule_optimizations(self, rule: SecurityRuleModel) -> List[Dict[str, Any]]:
        """Identifie les optimisations possibles pour une règle."""
        optimizations = []
        
        if rule.rule_type == 'firewall':
            # Optimisations pour règles firewall
            if 'any' in rule.content.lower() and rule.content.count('any') > 2:
                optimizations.append({
                    'type': 'specificity_improvement',
                    'description': 'Trop de wildcards "any", spécifier davantage'
                })
        
        elif rule.rule_type == 'ids':
            # Optimisations pour règles IDS
            if rule.content.count('content:') > 5:
                optimizations.append({
                    'type': 'content_reduction',
                    'description': 'Trop de patterns de contenu, optimiser les expressions'
                })
            
            if 'pcre:' in rule.content and len(rule.content) > 500:
                optimizations.append({
                    'type': 'regex_optimization',
                    'description': 'Expression régulière complexe, simplifier si possible'
                })
        
        # Optimisations générales
        if not rule.metadata or not rule.metadata.get('last_optimized'):
            optimizations.append({
                'type': 'metadata_update',
                'description': 'Ajouter métadonnées d\'optimisation'
            })
        
        return optimizations
    
    def _apply_rule_optimizations(self, rule: SecurityRuleModel, optimizations: List[Dict[str, Any]]) -> bool:
        """Applique les optimisations à une règle."""
        try:
            modified = False
            
            for optimization in optimizations:
                if optimization['type'] == 'metadata_update':
                    metadata = rule.metadata or {}
                    metadata['last_optimized'] = timezone.now().isoformat()
                    metadata['optimizations_applied'] = [opt['type'] for opt in optimizations]
                    rule.metadata = metadata
                    modified = True
                
                # Ajouter d'autres types d'optimisations selon les besoins
            
            if modified:
                rule.save()
                
                if self.verbose:
                    opt_types = [opt['type'] for opt in optimizations]
                    self.stdout.write(
                        f"⚡ Règle {rule.id} optimisée: {', '.join(opt_types)}"
                    )
            
            return modified
            
        except Exception as e:
            if self.verbose:
                self.stdout.write(
                    self.style.ERROR(f"❌ Erreur lors de l'optimisation de la règle {rule.id}: {str(e)}")
                )
            return False
    
    def _generate_optimization_report(
        self, 
        rules: List[SecurityRuleModel], 
        conflicts: List, 
        performance_analysis: Optional[Dict[str, Any]], 
        duration: timedelta
    ) -> Dict[str, Any]:
        """Génère un rapport complet d'optimisation."""
        report = {
            'optimization_summary': {
                'timestamp': timezone.now().isoformat(),
                'duration_seconds': duration.total_seconds(),
                'rules_analyzed': len(rules),
                'optimization_stats': self.optimization_stats.copy()
            },
            'conflict_analysis': {
                'total_conflicts': len(conflicts),
                'conflicts_by_type': {},
                'critical_conflicts': 0,
                'resolved_conflicts': self.optimization_stats['conflicts_resolved']
            },
            'performance_analysis': performance_analysis,
            'recommendations': [],
            'next_steps': []
        }
        
        # Analyser les conflits par type
        for conflict in conflicts:
            ctype = getattr(conflict, 'conflict_type', 'unknown')
            severity = getattr(conflict, 'severity', 'unknown')
            
            report['conflict_analysis']['conflicts_by_type'][ctype] = \
                report['conflict_analysis']['conflicts_by_type'].get(ctype, 0) + 1
            
            if severity == 'critical':
                report['conflict_analysis']['critical_conflicts'] += 1
        
        # Générer des recommandations
        if report['conflict_analysis']['critical_conflicts'] > 0:
            report['recommendations'].append(
                f"🚨 {report['conflict_analysis']['critical_conflicts']} conflits critiques nécessitent une attention immédiate"
            )
        
        if performance_analysis and performance_analysis.get('improvements_available'):
            report['recommendations'].append(
                "⚡ Optimisations de performance disponibles"
            )
        
        unresolved_conflicts = len(conflicts) - self.optimization_stats['conflicts_resolved']
        if unresolved_conflicts > 0:
            report['next_steps'].append(
                f"Examiner manuellement {unresolved_conflicts} conflits non résolus"
            )
        
        if self.optimization_stats['rules_optimized'] > 0:
            report['next_steps'].append(
                "Surveiller les performances après optimisation"
            )
        
        return report
    
    def _display_results(self, report: Dict[str, Any], output_format: str):
        """Affiche les résultats de l'optimisation."""
        if output_format == 'json':
            self.stdout.write(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            # Affichage texte formaté
            self.stdout.write(self.style.SUCCESS("\n🔧 RAPPORT D'OPTIMISATION DES RÈGLES DE SÉCURITÉ"))
            self.stdout.write("=" * 60)
            
            # Résumé
            summary = report['optimization_summary']
            self.stdout.write(f"\n📊 RÉSUMÉ")
            self.stdout.write(f"   Durée d'exécution: {summary['duration_seconds']:.2f}s")
            self.stdout.write(f"   Règles analysées: {summary['rules_analyzed']}")
            self.stdout.write(f"   Conflits détectés: {summary['optimization_stats']['conflicts_detected']}")
            self.stdout.write(f"   Conflits résolus: {summary['optimization_stats']['conflicts_resolved']}")
            self.stdout.write(f"   Règles optimisées: {summary['optimization_stats']['rules_optimized']}")
            self.stdout.write(f"   Règles consolidées: {summary['optimization_stats']['rules_consolidated']}")
            
            # Analyse des conflits
            conflict_analysis = report['conflict_analysis']
            if conflict_analysis['total_conflicts'] > 0:
                self.stdout.write(f"\n⚠️  CONFLITS DÉTECTÉS")
                for ctype, count in conflict_analysis['conflicts_by_type'].items():
                    self.stdout.write(f"   {ctype}: {count}")
                
                if conflict_analysis['critical_conflicts'] > 0:
                    self.stdout.write(
                        self.style.ERROR(f"   🚨 Conflits critiques: {conflict_analysis['critical_conflicts']}")
                    )
            
            # Performance
            if report['performance_analysis']:
                perf = report['performance_analysis']
                self.stdout.write(f"\n📈 PERFORMANCE")
                self.stdout.write(f"   Score global: {perf.get('performance_score', 'N/A')}")
                
                if perf.get('bottlenecks'):
                    self.stdout.write(f"   Goulots d'étranglement: {len(perf['bottlenecks'])}")
            
            # Recommandations
            if report['recommendations']:
                self.stdout.write(f"\n💡 RECOMMANDATIONS")
                for rec in report['recommendations']:
                    self.stdout.write(f"   • {rec}")
            
            # Prochaines étapes
            if report['next_steps']:
                self.stdout.write(f"\n🔄 PROCHAINES ÉTAPES")
                for step in report['next_steps']:
                    self.stdout.write(f"   • {step}")
            
            self.stdout.write("\n" + "=" * 60)
    
    def _export_report(self, report: Dict[str, Any], file_path: str):
        """Exporte le rapport vers un fichier."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.stdout.write(
                self.style.SUCCESS(f"📄 Rapport exporté vers: {file_path}")
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erreur lors de l'export: {str(e)}")
            )
    
    def _log_optimization_audit(self, options: Dict[str, Any]):
        """Enregistre l'audit de l'optimisation."""
        try:
            audit_details = {
                'command': 'optimize_security_rules',
                'options': {k: v for k, v in options.items() if k != 'verbosity'},
                'stats': self.optimization_stats.copy(),
                'timestamp': timezone.now().isoformat()
            }
            
            AuditLogModel.objects.create(
                action='optimization',
                target_type='security_rules',
                target_id=0,  # Global optimization
                user_id=None,  # System command
                ip_address='127.0.0.1',
                user_agent='Django Management Command',
                details=audit_details
            )
            
        except Exception as e:
            if self.verbose:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Erreur lors de l'audit: {str(e)}")
                )
    
    def _log_step(self, step_name: str):
        """Log une étape de l'optimisation."""
        if self.verbose:
            self.stdout.write(f"\n🔄 {step_name}...")