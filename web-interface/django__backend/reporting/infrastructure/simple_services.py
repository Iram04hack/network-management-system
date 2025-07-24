"""
Services simplifiés pour les tests sans dépendances lourdes.

Ce module contient des implémentations simplifiées des services avancés
qui peuvent fonctionner sans pandas, numpy, scikit-learn, etc.
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime
from django.conf import settings
from django.core.cache import cache

from ..domain.interfaces import (
    ReportStorageService,
    VisualizationService,
    AnalyticsService,
    DataIntegrationService,
    CacheService,
    ReportFormat,
    VisualizationType
)

logger = logging.getLogger(__name__)

class SimpleReportStorageService(ReportStorageService):
    """Service de stockage simplifié pour les tests."""
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or getattr(settings, 'REPORTS_STORAGE_PATH', '/tmp/reports')
        os.makedirs(self.storage_path, exist_ok=True)
    
    def store(self, content: Any, report_type: str, file_format: str, 
              metadata: Optional[Dict[str, Any]] = None) -> str:
        """Stocke un rapport de manière simplifiée."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{report_type}_{timestamp}.{file_format}"
            file_path = os.path.join(self.storage_path, filename)
            
            if isinstance(content, (dict, list)):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(content))
            
            return file_path
        except Exception as e:
            logger.error(f"Erreur lors du stockage: {e}")
            raise
    
    def retrieve(self, file_path: str) -> Optional[BinaryIO]:
        """Récupère un fichier stocké."""
        if os.path.exists(file_path):
            return open(file_path, 'rb')
        return None
    
    def delete(self, file_path: str) -> bool:
        """Supprime un fichier."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
        return False
    
    def archive(self, file_path: str, archive_location: str) -> bool:
        """Archive un fichier (implémentation simplifiée)."""
        return True
    
    def compress(self, file_path: str) -> str:
        """Compresse un fichier (implémentation simplifiée)."""
        return file_path

class SimpleVisualizationService(VisualizationService):
    """Service de visualisation simplifié pour les tests."""
    
    def create_visualization(self, data: Dict[str, Any], 
                           visualization_type: VisualizationType,
                           config: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une visualisation simplifiée."""
        return {
            'type': visualization_type.value if hasattr(visualization_type, 'value') else str(visualization_type),
            'config': config,
            'data_summary': {
                'records_count': len(data.get('values', [])) if isinstance(data.get('values'), list) else 0,
                'fields': list(data.keys())
            },
            'created_at': datetime.now().isoformat(),
            'simplified': True
        }
    
    def generate_interactive_dashboard(self, report_id: int,
                                     widgets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Génère un dashboard simplifié."""
        return {
            'report_id': report_id,
            'widgets_count': len(widgets),
            'widgets': [
                {
                    'type': w.get('type', 'unknown'),
                    'config': w.get('config', {}),
                    'simplified': True
                } for w in widgets
            ],
            'created_at': datetime.now().isoformat(),
            'simplified': True
        }
    
    def export_visualization(self, visualization_id: str, 
                           export_format: ReportFormat) -> str:
        """Exporte une visualisation (implémentation simplifiée)."""
        return f"/tmp/viz_{visualization_id}.{export_format.value}"

class SimpleAnalyticsService(AnalyticsService):
    """Service d'analyse simplifié pour les tests."""
    
    def detect_anomalies(self, data: List[Dict[str, Any]], 
                        config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Détection d'anomalies simplifiée."""
        # Implémentation très basique sans ML
        anomalies = []
        if data and len(data) > 2:
            # Simuler la détection d'anomalies
            for i, record in enumerate(data):
                if i % 10 == 0:  # Simuler 10% d'anomalies
                    anomalies.append({
                        'index': i,
                        'data': record,
                        'anomaly_score': 0.8,
                        'reason': 'Simulation d\'anomalie',
                        'simplified': True
                    })
        
        return anomalies
    
    def predict_trends(self, historical_data: List[Dict[str, Any]], 
                      prediction_horizon: int) -> Dict[str, Any]:
        """Prédiction de tendances simplifiée."""
        return {
            'predictions': {
                'trend': 'stable',
                'confidence': 0.7,
                'horizon_days': prediction_horizon
            },
            'data_points': len(historical_data),
            'simplified': True,
            'generated_at': datetime.now().isoformat()
        }
    
    def generate_insights(self, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Génération d'insights simplifiée."""
        insights = []
        
        values = report_data.get('values', [])
        if values:
            insights.append({
                'type': 'data_summary',
                'message': f'Le rapport contient {len(values)} enregistrements',
                'severity': 'info',
                'simplified': True
            })
            
            # Analyser les clés disponibles
            if values and isinstance(values[0], dict):
                fields = list(values[0].keys())
                insights.append({
                    'type': 'structure',
                    'message': f'Données structurées avec {len(fields)} champs: {", ".join(fields[:3])}{"..." if len(fields) > 3 else ""}',
                    'severity': 'info',
                    'simplified': True
                })
        
        return insights
    
    def correlation_analysis(self, datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyse de corrélation simplifiée."""
        return {
            'datasets_analyzed': len(datasets),
            'correlation_summary': 'Analyse simplifiée sans calculs mathématiques avancés',
            'simplified': True,
            'analysis_date': datetime.now().isoformat()
        }

class SimpleDataIntegrationService(DataIntegrationService):
    """Service d'intégration de données simplifié."""
    
    def integrate_data_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Intégration simplifiée de sources de données."""
        integrated_data = {}
        
        for i, source in enumerate(sources):
            source_name = source.get('name', f'source_{i}')
            source_data = source.get('data', [])
            integrated_data[source_name] = source_data
        
        return {
            'data': integrated_data,
            'metadata': {
                'sources_count': len(sources),
                'integration_date': datetime.now().isoformat(),
                'simplified': True
            }
        }
    
    def transform_data(self, data: Dict[str, Any], 
                      transformation_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transformation simplifiée des données."""
        transformed_data = data.copy()
        
        for rule in transformation_rules:
            rule_type = rule.get('type')
            if rule_type == 'rename':
                old_name = rule.get('old_name')
                new_name = rule.get('new_name')
                if old_name in transformed_data and new_name:
                    transformed_data[new_name] = transformed_data.pop(old_name)
        
        return transformed_data
    
    def validate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validation simplifiée de la qualité des données."""
        values = data.get('values', [])
        
        return {
            'overall_score': 85.0,  # Score simulé
            'metrics': {
                'records_count': len(values),
                'completeness': 'good',
                'consistency': 'acceptable'
            },
            'issues': [],
            'simplified': True,
            'validation_date': datetime.now().isoformat()
        }

class SimpleCacheService(CacheService):
    """Service de cache simplifié utilisant Django cache."""
    
    def __init__(self, cache_prefix: str = 'simple_reporting'):
        self.cache_prefix = cache_prefix
    
    def _make_key(self, key: str) -> str:
        return f"{self.cache_prefix}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        try:
            return cache.get(self._make_key(key))
        except Exception as e:
            logger.error(f"Erreur cache get: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            timeout = ttl or 3600
            cache.set(self._make_key(key), value, timeout)
            return True
        except Exception as e:
            logger.error(f"Erreur cache set: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        try:
            cache.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.error(f"Erreur cache delete: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        # Implémentation simplifiée
        logger.info(f"Invalidation pattern simplifié: {pattern}")
        return 0 