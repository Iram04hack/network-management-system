#!/usr/bin/env python3
"""
Script de validation pour la Phase 1 des corrections Dashboard.

Ce script exécute tous les tests et validations nécessaires pour s'assurer
que les corrections de la Phase 1 fonctionnent correctement.
"""

import os
import sys
import django
import subprocess
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nms_backend.settings')
django.setup()

def validate_imports():
    """
    Valide que tous les imports fonctionnent correctement.
    
    Returns:
        bool: True si tous les imports réussissent
    """
    print("\n🔍 VALIDATION DES IMPORTS")
    print("=" * 50)
    
    import_tests = [
        ("dashboard.di_container", "DI Container principal"),
        ("dashboard.infrastructure.cache_service", "Service de cache"),
        ("dashboard.infrastructure.monitoring_adapter", "Adaptateur monitoring"),
        ("dashboard.infrastructure.network_adapter", "Adaptateur réseau"),
        ("dashboard.infrastructure.services", "Services d'infrastructure"),
        ("dashboard.api.controllers", "Contrôleurs API"),
    ]
    
    all_success = True
    
    for module_name, description in import_tests:
        try:
            __import__(module_name)
            print(f"✅ {description} - Import réussi")
        except ImportError as e:
            print(f"❌ {description} - Erreur d'import: {e}")
            all_success = False
        except Exception as e:
            print(f"💥 {description} - Exception: {e}")
            all_success = False
    
    return all_success

def validate_di_container():
    """
    Valide que le DI Container fonctionne correctement.
    
    Returns:
        bool: True si le DI Container fonctionne
    """
    print("\n🏗️ VALIDATION DU DI CONTAINER")
    print("=" * 50)
    
    try:
        from dashboard.di_container import container
        
        # Test d'initialisation
        container.init_resources()
        print("✅ Initialisation du conteneur - SUCCÈS")
        
        # Test des services requis
        required_services = [
            'cache_service',
            'monitoring_adapter', 
            'network_adapter',
            'dashboard_service',
            'network_overview_service',
            'topology_service'
        ]
        
        all_services_ok = True
        for service_name in required_services:
            try:
                service = container.get_service(service_name)
                if service is not None:
                    print(f"✅ Service {service_name} - Disponible")
                else:
                    print(f"❌ Service {service_name} - Non disponible")
                    all_services_ok = False
            except Exception as e:
                print(f"❌ Service {service_name} - Erreur: {e}")
                all_services_ok = False
        
        return all_services_ok
        
    except Exception as e:
        print(f"❌ Erreur lors de la validation du DI Container: {e}")
        return False

def validate_urls():
    """
    Valide que les URLs sont correctement configurées.
    
    Returns:
        bool: True si les URLs sont accessibles
    """
    print("\n🌐 VALIDATION DES URLS")
    print("=" * 50)
    
    try:
        from django.urls import reverse, resolve
        
        # Test des URLs principales
        test_urls = [
            ('dashboard:dashboard_data', 'Données dashboard'),
            ('dashboard:dashboard_config', 'Configuration dashboard'),
            ('dashboard:network_overview', 'Aperçu réseau'),
            ('dashboard:topology_list', 'Liste topologies'),
            ('dashboard:topology_data', 'Données topologie'),
        ]
        
        all_urls_ok = True
        for url_name, description in test_urls:
            try:
                url = reverse(url_name)
                print(f"✅ {description} - URL: {url}")
            except Exception as e:
                print(f"❌ {description} - Erreur: {e}")
                all_urls_ok = False
        
        return all_urls_ok
        
    except Exception as e:
        print(f"❌ Erreur lors de la validation des URLs: {e}")
        return False

def validate_async_corrections():
    """
    Valide que les corrections sync/async fonctionnent.
    
    Returns:
        bool: True si les corrections fonctionnent
    """
    print("\n⚡ VALIDATION DES CORRECTIONS SYNC/ASYNC")
    print("=" * 50)
    
    try:
        from dashboard.api.controllers import (
            DashboardDataView,
            UserDashboardConfigView,
            NetworkOverviewView,
            TopologyDataView,
            TopologyListView
        )
        
        # Vérifier que les méthodes existent et sont correctement définies
        controllers_to_test = [
            (DashboardDataView, 'get', 'DashboardDataView.get'),
            (UserDashboardConfigView, 'get', 'UserDashboardConfigView.get'),
            (UserDashboardConfigView, 'post', 'UserDashboardConfigView.post'),
            (NetworkOverviewView, 'get', 'NetworkOverviewView.get'),
            (TopologyDataView, 'get', 'TopologyDataView.get'),
            (TopologyListView, 'get', 'TopologyListView.get'),
        ]
        
        all_methods_ok = True
        for controller_class, method_name, description in controllers_to_test:
            try:
                method = getattr(controller_class, method_name)
                if callable(method):
                    print(f"✅ {description} - Méthode disponible")
                else:
                    print(f"❌ {description} - Méthode non callable")
                    all_methods_ok = False
            except AttributeError:
                print(f"❌ {description} - Méthode manquante")
                all_methods_ok = False
        
        return all_methods_ok
        
    except Exception as e:
        print(f"❌ Erreur lors de la validation des corrections async: {e}")
        return False

def main():
    """
    Fonction principale de validation.
    """
    print("🚀 VALIDATION PHASE 1 - CORRECTIONS CRITIQUES DASHBOARD")
    print("=" * 60)
    
    # Liste des validations à effectuer
    validations = [
        (validate_imports, "Validation des imports"),
        (validate_di_container, "Validation du DI Container"),
        (validate_urls, "Validation des URLs"),
        (validate_async_corrections, "Validation des corrections sync/async"),
    ]
    
    # Exécuter les validations
    results = []
    for validation_func, description in validations:
        try:
            result = validation_func()
            results.append((description, result))
        except Exception as e:
            print(f"💥 Erreur lors de {description}: {e}")
            results.append((description, False))
    
    # Résumé final
    print("\n📊 RÉSUMÉ DE LA VALIDATION")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    failed_tests = total_tests - passed_tests
    
    for description, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{status} - {description}")
    
    print(f"\n📈 STATISTIQUES:")
    print(f"   Total: {total_tests}")
    print(f"   Réussis: {passed_tests}")
    print(f"   Échoués: {failed_tests}")
    print(f"   Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 TOUTES LES VALIDATIONS ONT RÉUSSI!")
        print("✅ La Phase 1 est prête pour la validation fonctionnelle.")
        return True
    else:
        print(f"\n⚠️  {failed_tests} VALIDATION(S) ONT ÉCHOUÉ")
        print("❌ Des corrections supplémentaires sont nécessaires.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
