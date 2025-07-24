"""
Validateur et améliorateur automatique de documentation Swagger pour api_views.

Ce script analyse tous les ViewSets et vues API du module api_views pour s'assurer
que chaque endpoint a une documentation Swagger complète et cohérente.
"""

import inspect
import sys
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

# Ajouter le chemin du projet Django
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import django
    from django.conf import settings
    
    # Configuration Django minimale pour l'introspection
    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nms_backend.settings')
        django.setup()
except:
    pass

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema


class SwaggerDocumentationValidator:
    """Validateur de documentation Swagger pour les APIs."""
    
    def __init__(self):
        self.issues = []
        self.recommendations = []
        self.stats = {
            'total_viewsets': 0,
            'documented_methods': 0,
            'undocumented_methods': 0,
            'missing_summaries': 0,
            'missing_descriptions': 0,
            'inconsistent_tags': 0
        }
    
    def validate_all_viewsets(self):
        """Valide tous les ViewSets du module api_views."""
        print("🔍 === VALIDATION SWAGGER API_VIEWS ===\n")
        
        # Import dynamique de tous les ViewSets
        viewsets_to_check = self._import_all_viewsets()
        
        for viewset_name, viewset_class in viewsets_to_check.items():
            print(f"📋 Analyse de {viewset_name}...")
            self._validate_viewset(viewset_name, viewset_class)
            self.stats['total_viewsets'] += 1
        
        self._print_report()
        return self.issues, self.recommendations
    
    def _import_all_viewsets(self) -> Dict[str, Any]:
        """Import tous les ViewSets disponibles."""
        viewsets_dict = {}
        
        try:
            # Import des ViewSets dashboard
            from api_views.views.dashboard_views import (
                DashboardViewSet, DashboardWidgetViewSet
            )
            viewsets_dict.update({
                'DashboardViewSet': DashboardViewSet,
                'DashboardWidgetViewSet': DashboardWidgetViewSet,
            })
            
            # Import des ViewSets device management
            from api_views.views.device_management_views import (
                DeviceManagementViewSet
            )
            viewsets_dict.update({
                'DeviceManagementViewSet': DeviceManagementViewSet,
            })
            
            # Import des ViewSets search
            from api_views.views.search_views import (
                GlobalSearchViewSet, ResourceSearchViewSet, SearchHistoryViewSet
            )
            viewsets_dict.update({
                'GlobalSearchViewSet': GlobalSearchViewSet,
                'ResourceSearchViewSet': ResourceSearchViewSet,
                'SearchHistoryViewSet': SearchHistoryViewSet,
            })
            
            # Import des ViewSets topology
            from api_views.views.topology_discovery_views import (
                TopologyDiscoveryViewSet
            )
            viewsets_dict.update({
                'TopologyDiscoveryViewSet': TopologyDiscoveryViewSet,
            })
            
            # Import des ViewSets monitoring
            from api_views.views.prometheus_views import PrometheusViewSet
            from api_views.views.grafana_views import GrafanaViewSet
            from api_views.views.security_views import Fail2banViewSet, SuricataViewSet
            
            viewsets_dict.update({
                'PrometheusViewSet': PrometheusViewSet,
                'GrafanaViewSet': GrafanaViewSet,
                'Fail2banViewSet': Fail2banViewSet,
                'SuricataViewSet': SuricataViewSet,
            })
            
        except ImportError as e:
            print(f"⚠️ Erreur d'import: {e}")
        
        return viewsets_dict
    
    def _validate_viewset(self, name: str, viewset_class: Any):
        """Valide la documentation Swagger d'un ViewSet."""
        methods_to_check = self._get_viewset_methods(viewset_class)
        
        for method_name, method_func in methods_to_check.items():
            self._validate_method_documentation(name, method_name, method_func)
    
    def _get_viewset_methods(self, viewset_class: Any) -> Dict[str, Any]:
        """Récupère toutes les méthodes à documenter d'un ViewSet."""
        methods = {}
        
        # Méthodes CRUD standard
        crud_methods = ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']
        for method_name in crud_methods:
            if hasattr(viewset_class, method_name):
                methods[method_name] = getattr(viewset_class, method_name)
        
        # Actions personnalisées (@action)
        for attr_name in dir(viewset_class):
            attr = getattr(viewset_class, attr_name)
            if hasattr(attr, 'mapping') and hasattr(attr, 'detail'):
                # C'est une action personnalisée
                methods[attr_name] = attr
        
        return methods
    
    def _validate_method_documentation(self, viewset_name: str, method_name: str, method_func: Any):
        """Valide la documentation d'une méthode spécifique."""
        issues = []
        
        # Vérifier si la méthode a un décorateur swagger_auto_schema
        has_swagger_decorator = self._has_swagger_decorator(method_func)
        
        if not has_swagger_decorator:
            issues.append(f"❌ {viewset_name}.{method_name}: Aucun décorateur @swagger_auto_schema")
            self.stats['undocumented_methods'] += 1
        else:
            self.stats['documented_methods'] += 1
            
            # Vérifier les éléments de documentation
            swagger_info = self._extract_swagger_info(method_func)
            
            if not swagger_info.get('operation_summary'):
                issues.append(f"⚠️ {viewset_name}.{method_name}: operation_summary manquant")
                self.stats['missing_summaries'] += 1
                
            if not swagger_info.get('operation_description'):
                issues.append(f"⚠️ {viewset_name}.{method_name}: operation_description manquant")
                self.stats['missing_descriptions'] += 1
                
            # Vérifier le tag
            tags = swagger_info.get('tags', [])
            if not tags or 'views' not in tags:
                issues.append(f"⚠️ {viewset_name}.{method_name}: Tag 'views' manquant")
                self.stats['inconsistent_tags'] += 1
        
        if issues:
            self.issues.extend(issues)
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"  ✅ {viewset_name}.{method_name}: Documentation complète")
    
    def _has_swagger_decorator(self, method_func: Any) -> bool:
        """Vérifie si une méthode a un décorateur swagger_auto_schema."""
        return hasattr(method_func, '_swagger_auto_schema')
    
    def _extract_swagger_info(self, method_func: Any) -> Dict[str, Any]:
        """Extrait les informations Swagger d'une méthode."""
        swagger_info = {}
        
        if hasattr(method_func, '_swagger_auto_schema'):
            schema_info = method_func._swagger_auto_schema
            swagger_info.update({
                'operation_summary': getattr(schema_info, 'operation_summary', None),
                'operation_description': getattr(schema_info, 'operation_description', None),
                'tags': getattr(schema_info, 'tags', []),
                'responses': getattr(schema_info, 'responses', {}),
            })
        
        return swagger_info
    
    def _print_report(self):
        """Affiche le rapport final."""
        print("\n" + "="*60)
        print("📊 === RAPPORT DE VALIDATION SWAGGER ===")
        print("="*60)
        
        print(f"\n📈 **STATISTIQUES GLOBALES**")
        print(f"  • ViewSets analysés: {self.stats['total_viewsets']}")
        print(f"  • Méthodes documentées: {self.stats['documented_methods']}")
        print(f"  • Méthodes non documentées: {self.stats['undocumented_methods']}")
        print(f"  • Summaires manquants: {self.stats['missing_summaries']}")
        print(f"  • Descriptions manquantes: {self.stats['missing_descriptions']}")
        print(f"  • Tags incohérents: {self.stats['inconsistent_tags']}")
        
        # Calcul du score de qualité
        total_methods = self.stats['documented_methods'] + self.stats['undocumented_methods']
        if total_methods > 0:
            quality_score = (self.stats['documented_methods'] / total_methods) * 100
            print(f"\n🎯 **SCORE DE QUALITÉ**: {quality_score:.1f}%")
            
            if quality_score >= 90:
                print("🏆 Excellente documentation!")
            elif quality_score >= 75:
                print("👍 Bonne documentation, quelques améliorations possibles")
            elif quality_score >= 50:
                print("⚠️ Documentation moyenne, amélioration recommandée")
            else:
                print("❌ Documentation insuffisante, action requise")
        
        print(f"\n🔧 **RECOMMANDATIONS**")
        if self.stats['undocumented_methods'] > 0:
            print(f"  • Ajouter @swagger_auto_schema à {self.stats['undocumented_methods']} méthodes")
        if self.stats['missing_summaries'] > 0:
            print(f"  • Ajouter operation_summary à {self.stats['missing_summaries']} méthodes")
        if self.stats['missing_descriptions'] > 0:
            print(f"  • Ajouter operation_description à {self.stats['missing_descriptions']} méthodes")
        if self.stats['inconsistent_tags'] > 0:
            print(f"  • Standardiser les tags pour {self.stats['inconsistent_tags']} méthodes")
        
        if not any([
            self.stats['undocumented_methods'],
            self.stats['missing_summaries'], 
            self.stats['missing_descriptions'],
            self.stats['inconsistent_tags']
        ]):
            print("  ✅ Aucune amélioration nécessaire - Documentation parfaite!")


def main():
    """Point d'entrée principal."""
    print("🚀 === VALIDATEUR SWAGGER API_VIEWS ===\n")
    
    validator = SwaggerDocumentationValidator()
    issues, recommendations = validator.validate_all_viewsets()
    
    print("\n" + "="*60)
    print("✨ Validation terminée!")
    print("="*60)
    
    return len(issues) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 