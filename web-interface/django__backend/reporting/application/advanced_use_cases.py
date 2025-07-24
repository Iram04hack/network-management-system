"""
Cas d'utilisation avancés pour le module de reporting.

Ce module contient les cas d'utilisation pour les fonctionnalités avancées
comme la visualisation, l'analyse de données et l'intégration multi-sources.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..domain.interfaces import (
    ReportRepository,
    VisualizationService,
    AnalyticsService,
    DataIntegrationService,
    CacheService,
    VisualizationType,
    ReportFormat
)

logger = logging.getLogger(__name__)

class CreateVisualizationUseCase:
    """Cas d'utilisation pour créer des visualisations interactives."""
    
    def __init__(self, 
                 report_repository: ReportRepository,
                 visualization_service: VisualizationService,
                 cache_service: CacheService):
        self.report_repository = report_repository
        self.visualization_service = visualization_service
        self.cache_service = cache_service
    
    def execute(self, report_id: int, visualization_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une visualisation pour un rapport.
        
        Args:
            report_id: ID du rapport
            visualization_config: Configuration de la visualisation
            
        Returns:
            Configuration de la visualisation créée
        """
        try:
            # Vérifier le cache d'abord
            cache_key = f"visualization:{report_id}:{hash(str(visualization_config))}"
            cached_result = self.cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Visualisation trouvée dans le cache pour le rapport {report_id}")
                return cached_result
            
            # Récupérer le rapport
            report = self.report_repository.get_by_id(report_id)
            if not report:
                raise ValueError(f"Rapport {report_id} introuvable")
            
            # Déterminer le type de visualisation
            viz_type = VisualizationType(visualization_config.get('type', 'chart'))
            
            # Créer la visualisation
            visualization = self.visualization_service.create_visualization(
                data=report['content'],
                visualization_type=viz_type,
                config=visualization_config
            )
            
            # Ajouter les métadonnées du rapport
            visualization['report_metadata'] = {
                'report_id': report_id,
                'report_title': report['title'],
                'report_type': report['report_type'],
                'created_at': datetime.now().isoformat()
            }
            
            # Mettre en cache
            self.cache_service.set(cache_key, visualization, ttl=3600)  # 1 heure
            
            logger.info(f"Visualisation créée pour le rapport {report_id}")
            return visualization
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la visualisation pour le rapport {report_id}: {e}")
            raise

class CreateDashboardUseCase:
    """Cas d'utilisation pour créer des dashboards interactifs."""
    
    def __init__(self, 
                 report_repository: ReportRepository,
                 visualization_service: VisualizationService,
                 cache_service: CacheService):
        self.report_repository = report_repository
        self.visualization_service = visualization_service
        self.cache_service = cache_service
    
    def execute(self, report_id: int, dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un dashboard interactif pour un rapport.
        
        Args:
            report_id: ID du rapport
            dashboard_config: Configuration du dashboard
            
        Returns:
            Configuration du dashboard créé
        """
        try:
            # Vérifier le cache
            cache_key = f"dashboard:{report_id}:{hash(str(dashboard_config))}"
            cached_result = self.cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Dashboard trouvé dans le cache pour le rapport {report_id}")
                return cached_result
            
            # Récupérer le rapport
            report = self.report_repository.get_by_id(report_id)
            if not report:
                raise ValueError(f"Rapport {report_id} introuvable")
            
            # Récupérer les widgets du dashboard
            widgets = dashboard_config.get('widgets', [])
            
            # Générer le dashboard
            dashboard = self.visualization_service.generate_interactive_dashboard(
                report_id=report_id,
                widgets=widgets
            )
            
            # Ajouter la configuration globale
            dashboard['layout'] = dashboard_config.get('layout', {})
            dashboard['title'] = dashboard_config.get('title', f"Dashboard - {report['title']}")
            
            # Mettre en cache
            self.cache_service.set(cache_key, dashboard, ttl=1800)  # 30 minutes
            
            logger.info(f"Dashboard créé pour le rapport {report_id}")
            return dashboard
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du dashboard pour le rapport {report_id}: {e}")
            raise

class AnalyzeDataUseCase:
    """Cas d'utilisation pour l'analyse avancée de données."""
    
    def __init__(self, 
                 analytics_service: AnalyticsService,
                 cache_service: CacheService):
        self.analytics_service = analytics_service
        self.cache_service = cache_service
    
    def execute(self, data: List[Dict[str, Any]], analysis_type: str, 
                config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Effectue une analyse avancée sur les données.
        
        Args:
            data: Données à analyser
            analysis_type: Type d'analyse ('anomalies', 'trends', 'insights', 'correlation')
            config: Configuration de l'analyse
            
        Returns:
            Résultats de l'analyse
        """
        try:
            # Vérifier le cache
            data_hash = hash(str(data) + str(config))
            cache_key = f"analysis:{analysis_type}:{data_hash}"
            cached_result = self.cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Résultats d'analyse trouvés dans le cache pour {analysis_type}")
                return cached_result
            
            # Effectuer l'analyse selon le type
            if analysis_type == 'anomalies':
                results = self.analytics_service.detect_anomalies(data, config)
            elif analysis_type == 'trends':
                prediction_horizon = config.get('prediction_horizon', 30)
                results = self.analytics_service.predict_trends(data, prediction_horizon)
            elif analysis_type == 'insights':
                # Pour les insights, data doit être formaté comme un rapport
                report_data = {'values': data}
                results = self.analytics_service.generate_insights(report_data)
            elif analysis_type == 'correlation':
                # Pour la corrélation, data doit être une liste de datasets
                datasets = [{'values': data}] if not isinstance(data[0], dict) or 'values' not in data[0] else data
                results = self.analytics_service.correlation_analysis(datasets)
            else:
                raise ValueError(f"Type d'analyse non supporté: {analysis_type}")
            
            # Ajouter les métadonnées
            analysis_results = {
                'analysis_type': analysis_type,
                'config': config,
                'results': results,
                'data_size': len(data),
                'analyzed_at': datetime.now().isoformat()
            }
            
            # Mettre en cache
            cache_ttl = 1800 if analysis_type in ['insights', 'anomalies'] else 3600  # 30min ou 1h
            self.cache_service.set(cache_key, analysis_results, ttl=cache_ttl)
            
            logger.info(f"Analyse {analysis_type} terminée sur {len(data)} enregistrements")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse {analysis_type}: {e}")
            raise

class IntegrateDataUseCase:
    """Cas d'utilisation pour l'intégration de données multi-sources."""
    
    def __init__(self, 
                 data_integration_service: DataIntegrationService,
                 cache_service: CacheService):
        self.data_integration_service = data_integration_service
        self.cache_service = cache_service
    
    def execute(self, sources: List[Dict[str, Any]], 
                transformation_rules: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Intègre des données de sources multiples.
        
        Args:
            sources: Liste des sources de données
            transformation_rules: Règles de transformation optionnelles
            
        Returns:
            Données intégrées
        """
        try:
            # Vérifier le cache
            sources_hash = hash(str(sources) + str(transformation_rules))
            cache_key = f"integration:{sources_hash}"
            cached_result = self.cache_service.get(cache_key)
            if cached_result:
                logger.info("Données intégrées trouvées dans le cache")
                return cached_result
            
            # Intégrer les données
            integrated_data = self.data_integration_service.integrate_data_sources(sources)
            
            # Appliquer les transformations si spécifiées
            if transformation_rules:
                integrated_data['data'] = self.data_integration_service.transform_data(
                    integrated_data['data'], 
                    transformation_rules
                )
                integrated_data['metadata']['transformations_applied'] = len(transformation_rules)
            
            # Valider la qualité des données
            quality_report = {}
            for source_name, source_data in integrated_data['data'].items():
                if isinstance(source_data, list) and source_data:
                    quality = self.data_integration_service.validate_data_quality({'values': source_data})
                    quality_report[source_name] = quality
            
            integrated_data['quality_report'] = quality_report
            
            # Ajouter les métadonnées de traitement
            integrated_data['metadata']['processed_at'] = datetime.now().isoformat()
            integrated_data['metadata']['cache_key'] = cache_key
            
            # Mettre en cache (courte durée car les données peuvent changer fréquemment)
            self.cache_service.set(cache_key, integrated_data, ttl=900)  # 15 minutes
            
            logger.info(f"Intégration de {len(sources)} sources terminée")
            return integrated_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration des données: {e}")
            raise

class GenerateInsightsUseCase:
    """Cas d'utilisation pour générer des insights automatiques."""
    
    def __init__(self, 
                 report_repository: ReportRepository,
                 analytics_service: AnalyticsService,
                 cache_service: CacheService):
        self.report_repository = report_repository
        self.analytics_service = analytics_service
        self.cache_service = cache_service
    
    def execute(self, report_id: int, 
                analysis_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Génère des insights automatiques pour un rapport.
        
        Args:
            report_id: ID du rapport
            analysis_config: Configuration de l'analyse
            
        Returns:
            Insights générés
        """
        try:
            # Configuration par défaut
            config = analysis_config or {}
            
            # Vérifier le cache
            cache_key = f"insights:{report_id}:{hash(str(config))}"
            cached_result = self.cache_service.get(cache_key)
            if cached_result:
                logger.info(f"Insights trouvés dans le cache pour le rapport {report_id}")
                return cached_result
            
            # Récupérer le rapport
            report = self.report_repository.get_by_id(report_id)
            if not report:
                raise ValueError(f"Rapport {report_id} introuvable")
            
            # Générer les insights
            insights = self.analytics_service.generate_insights(report['content'])
            
            # Ajouter des analyses complémentaires si demandées
            additional_analyses = {}
            
            if config.get('include_anomalies', False) and 'values' in report['content']:
                try:
                    anomalies = self.analytics_service.detect_anomalies(
                        report['content']['values'], 
                        config.get('anomaly_config', {})
                    )
                    additional_analyses['anomalies'] = {
                        'count': len(anomalies),
                        'details': anomalies[:5],  # Limiter pour éviter les gros objets
                        'summary': f"{len(anomalies)} anomalies détectées"
                    }
                except Exception as e:
                    logger.warning(f"Impossible de détecter les anomalies: {e}")
            
            if config.get('include_trends', False) and 'values' in report['content']:
                try:
                    trends = self.analytics_service.predict_trends(
                        report['content']['values'],
                        config.get('prediction_horizon', 30)
                    )
                    additional_analyses['trends'] = trends
                except Exception as e:
                    logger.warning(f"Impossible de prédire les tendances: {e}")
            
            # Structurer les résultats
            insights_report = {
                'report_id': report_id,
                'report_title': report['title'],
                'insights': insights,
                'additional_analyses': additional_analyses,
                'generated_at': datetime.now().isoformat(),
                'config': config
            }
            
            # Mettre en cache
            self.cache_service.set(cache_key, insights_report, ttl=2700)  # 45 minutes
            
            logger.info(f"Insights générés pour le rapport {report_id}: {len(insights)} insights trouvés")
            return insights_report
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'insights pour le rapport {report_id}: {e}")
            raise

class OptimizeReportPerformanceUseCase:
    """Cas d'utilisation pour optimiser les performances des rapports."""
    
    def __init__(self, 
                 report_repository: ReportRepository,
                 cache_service: CacheService):
        self.report_repository = report_repository
        self.cache_service = cache_service
    
    def execute(self, report_filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyse et optimise les performances des rapports.
        
        Args:
            report_filters: Filtres pour sélectionner les rapports à analyser
            
        Returns:
            Rapport d'optimisation
        """
        try:
            # Récupérer les rapports
            reports = self.report_repository.list(report_filters)
            
            optimization_report = {
                'analyzed_reports': len(reports),
                'optimizations': [],
                'cache_stats': {},
                'performance_metrics': {},
                'recommendations': [],
                'analyzed_at': datetime.now().isoformat()
            }
            
            # Analyser les performances du cache
            cache_keys_checked = 0
            cache_hits = 0
            
            for report in reports:
                report_id = report['id']
                
                # Vérifier les clés de cache liées à ce rapport
                cache_keys = [
                    f"visualization:{report_id}:*",
                    f"dashboard:{report_id}:*",
                    f"insights:{report_id}:*"
                ]
                
                for key_pattern in cache_keys:
                    cache_keys_checked += 1
                    # Note: L'implémentation réelle dépendrait du backend de cache
                    # Pour Redis, on pourrait utiliser SCAN
                
            # Recommandations générales
            if len(reports) > 100:
                optimization_report['recommendations'].append({
                    'type': 'cache_optimization',
                    'message': 'Considérer l\'utilisation d\'un cache Redis pour améliorer les performances',
                    'priority': 'medium'
                })
            
            if any(len(str(report.get('content', {}))) > 100000 for report in reports):
                optimization_report['recommendations'].append({
                    'type': 'data_optimization',
                    'message': 'Certains rapports contiennent beaucoup de données. Considérer la pagination ou la compression',
                    'priority': 'high'
                })
            
            # Statistiques de performance
            optimization_report['performance_metrics'] = {
                'average_report_size': sum(len(str(r.get('content', {}))) for r in reports) / len(reports) if reports else 0,
                'largest_report_size': max((len(str(r.get('content', {}))) for r in reports), default=0),
                'cache_keys_checked': cache_keys_checked,
                'estimated_cache_hit_ratio': cache_hits / cache_keys_checked if cache_keys_checked > 0 else 0
            }
            
            logger.info(f"Analyse de performance terminée pour {len(reports)} rapports")
            return optimization_report
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de performance: {e}")
            raise 