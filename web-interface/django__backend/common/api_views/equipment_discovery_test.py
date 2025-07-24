"""
🔧 ENDPOINT DE TEST : Service de découverte d'équipements amélioré

Ce fichier contient l'endpoint de test pour valider les corrections du système de découverte d'IPs.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
import asyncio
import logging

from .equipment_discovery_enhanced import enhanced_equipment_discovery_service

logger = logging.getLogger(__name__)

@swagger_auto_schema(
    method='post',
    operation_description="🔧 TEST - Découverte d'équipement avec récupération d'IPs améliorée",
    manual_parameters=[
        openapi.Parameter('project_id', openapi.IN_PATH, description="ID du projet GNS3", type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('equipment_id', openapi.IN_PATH, description="ID de l'équipement", type=openapi.TYPE_STRING, required=True),
    ],
    responses={
        200: openapi.Response(
            description="Découverte d'équipement avec IPs réelles",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'equipment_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                    'ip_addresses': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'discovery_methods': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                    'discovery_status': openapi.Schema(type=openapi.TYPE_STRING),
                    'network_info': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'connectivity_tests': openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )
        )
    },
    tags=['Common - Infrastructure - TEST']
)
@api_view(['POST'])
@permission_classes([])
def test_enhanced_equipment_discovery(request, project_id, equipment_id):
    """
    🔧 TEST - Découverte d'équipement avec récupération d'IPs améliorée.
    
    Utilise le service amélioré pour tester la récupération d'IPs réelles.
    """
    try:
        logger.info(f"🔍 TEST - Démarrage découverte améliorée pour équipement {equipment_id}")
        
        # Découverte asynchrone avec le service amélioré
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            equipment_data = loop.run_until_complete(
                enhanced_equipment_discovery_service.discover_equipment_with_real_ips(project_id, equipment_id)
            )
        finally:
            loop.close()
        
        # Extraire les informations importantes pour la réponse
        response_data = {
            'test_mode': True,
            'equipment_id': equipment_data.get('equipment_id'),
            'name': equipment_data.get('name', 'Unknown'),
            'node_type': equipment_data.get('node_type', 'unknown'),
            'status': equipment_data.get('status', 'unknown'),
            'discovery_status': equipment_data.get('discovery_status', 'unknown'),
            'discovery_timestamp': equipment_data.get('discovery_timestamp'),
            'discovery_completion_time': equipment_data.get('discovery_completion_time'),
            
            # Informations sur les IPs découvertes
            'ip_addresses': equipment_data.get('network_info', {}).get('ip_addresses', []),
            'ip_discovery_methods': equipment_data.get('ip_discovery_methods', []),
            'ip_discovery_results': equipment_data.get('ip_discovery_results', {}),
            
            # Tests de connectivité
            'connectivity_tests': equipment_data.get('network_info', {}).get('connectivity_tests', {}),
            
            # Interfaces réseau
            'interfaces': equipment_data.get('network_info', {}).get('interfaces', []),
            
            # Informations SNMP
            'snmp_available': equipment_data.get('snmp_data', {}).get('snmp_available', False),
            'snmp_community': equipment_data.get('snmp_data', {}).get('active_community', None),
            
            # Statistiques
            'stats': {
                'total_ips_discovered': len(equipment_data.get('network_info', {}).get('ip_addresses', [])),
                'methods_used': len(equipment_data.get('ip_discovery_methods', [])),
                'interfaces_count': len(equipment_data.get('network_info', {}).get('interfaces', [])),
                'connectivity_tests_count': len(equipment_data.get('network_info', {}).get('connectivity_tests', {}))
            }
        }
        
        # Ajouter les détails complets si demandé
        if request.GET.get('full_details', '').lower() == 'true':
            response_data['full_equipment_data'] = equipment_data
        
        logger.info(f"✅ TEST - Découverte terminée pour {response_data['name']}: {response_data['stats']['total_ips_discovered']} IPs trouvées")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ TEST - Erreur découverte équipement {equipment_id}: {e}")
        return Response(
            {
                'test_mode': True,
                'error': f'Erreur lors de la découverte de l\'équipement: {str(e)}',
                'equipment_id': equipment_id,
                'project_id': project_id,
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="🔧 TEST - Découverte complète de tous les équipements avec IPs améliorées",
    manual_parameters=[
        openapi.Parameter('project_id', openapi.IN_PATH, description="ID du projet GNS3", type=openapi.TYPE_STRING, required=True),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'max_concurrent': openapi.Schema(type=openapi.TYPE_INTEGER, default=3),
            'include_full_details': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
        }
    ),
    responses={
        200: openapi.Response(
            description="Découverte complète avec IPs réelles",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'project_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'total_equipment': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'equipment_with_ips': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'equipment_without_ips': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_ips_discovered': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'discovery_summary': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'equipment_details': openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )
        )
    },
    tags=['Common - Infrastructure - TEST']
)
@api_view(['POST'])
@permission_classes([])
def test_enhanced_project_discovery(request, project_id):
    """
    🔧 TEST - Découverte complète de tous les équipements avec IPs améliorées.
    
    Teste la découverte sur tous les équipements du projet pour identifier
    le nombre d'équipements avec des IPs valides pour les tests de sécurité.
    """
    try:
        logger.info(f"🔍 TEST - Démarrage découverte complète pour projet {project_id}")
        
        # Paramètres de configuration
        max_concurrent = request.data.get('max_concurrent', 3)
        include_full_details = request.data.get('include_full_details', False)
        
        start_time = timezone.now()
        
        # Récupérer la liste des équipements
        from api_clients.network.gns3_client import GNS3Client
        gns3_client = GNS3Client()
        project_info = gns3_client.get_project(project_id)
        nodes = gns3_client.get_nodes(project_id)
        
        discovery_results = {
            'test_mode': True,
            'project_id': project_id,
            'project_name': project_info.get('name', 'Unknown'),
            'discovery_start_time': start_time.isoformat(),
            'total_equipment': len(nodes),
            'equipment_with_ips': 0,
            'equipment_without_ips': 0,
            'total_ips_discovered': 0,
            'equipment_details': {},
            'discovery_summary': {},
            'ip_distribution': {},
            'connectivity_summary': {}
        }
        
        async def discover_all_equipment():
            """Fonction asynchrone pour découvrir tous les équipements."""
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def discover_single_equipment(node):
                async with semaphore:
                    try:
                        node_id = node.get('node_id')
                        equipment_data = await enhanced_equipment_discovery_service.discover_equipment_with_real_ips(
                            project_id, node_id
                        )
                        return equipment_data
                    except Exception as e:
                        logger.error(f"❌ Erreur découverte équipement {node.get('node_id')}: {e}")
                        return None
            
            # Exécuter la découverte en parallèle
            tasks = [discover_single_equipment(node) for node in nodes]
            equipment_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return equipment_results
        
        # Exécuter la découverte asynchrone
        equipment_results = asyncio.run(discover_all_equipment())
        
        # Traiter les résultats
        ip_distribution = {}
        connectivity_summary = {
            'total_ips': 0,
            'responsive_ips': 0,
            'snmp_enabled': 0,
            'services_detected': {}
        }
        
        for result in equipment_results:
            if result and not isinstance(result, Exception):
                equipment_id = result.get('equipment_id')
                equipment_name = result.get('name', 'Unknown')
                
                # Compter les IPs
                ips = result.get('network_info', {}).get('ip_addresses', [])
                ip_count = len(ips)
                
                if ip_count > 0:
                    discovery_results['equipment_with_ips'] += 1
                    discovery_results['total_ips_discovered'] += ip_count
                    
                    # Distribution des IPs
                    ip_distribution[equipment_name] = {
                        'ip_count': ip_count,
                        'ips': ips,
                        'methods_used': result.get('ip_discovery_methods', []),
                        'snmp_available': result.get('snmp_data', {}).get('snmp_available', False)
                    }
                    
                    # Analyse de connectivité
                    connectivity_tests = result.get('network_info', {}).get('connectivity_tests', {})
                    connectivity_summary['total_ips'] += ip_count
                    
                    for ip, connectivity in connectivity_tests.items():
                        if connectivity.get('ping_success', False):
                            connectivity_summary['responsive_ips'] += 1
                        
                        # Services détectés
                        services = connectivity.get('services_detected', [])
                        for service in services:
                            if service not in connectivity_summary['services_detected']:
                                connectivity_summary['services_detected'][service] = 0
                            connectivity_summary['services_detected'][service] += 1
                    
                    # SNMP
                    if result.get('snmp_data', {}).get('snmp_available', False):
                        connectivity_summary['snmp_enabled'] += 1
                    
                else:
                    discovery_results['equipment_without_ips'] += 1
                    ip_distribution[equipment_name] = {
                        'ip_count': 0,
                        'ips': [],
                        'methods_used': result.get('ip_discovery_methods', []),
                        'snmp_available': False
                    }
                
                # Ajouter les détails complets si demandé
                if include_full_details:
                    discovery_results['equipment_details'][equipment_id] = result
                else:
                    # Résumé compact
                    discovery_results['equipment_details'][equipment_id] = {
                        'name': equipment_name,
                        'node_type': result.get('node_type', 'unknown'),
                        'status': result.get('status', 'unknown'),
                        'ip_count': ip_count,
                        'ips': ips,
                        'discovery_methods': result.get('ip_discovery_methods', []),
                        'snmp_available': result.get('snmp_data', {}).get('snmp_available', False),
                        'discovery_status': result.get('discovery_status', 'unknown')
                    }
        
        # Calculer le résumé
        success_rate = (discovery_results['equipment_with_ips'] / len(nodes) * 100) if nodes else 0
        ip_success_rate = (connectivity_summary['responsive_ips'] / connectivity_summary['total_ips'] * 100) if connectivity_summary['total_ips'] > 0 else 0
        
        discovery_results['discovery_summary'] = {
            'success_rate': success_rate,
            'ip_success_rate': ip_success_rate,
            'average_ips_per_equipment': discovery_results['total_ips_discovered'] / len(nodes) if nodes else 0,
            'equipment_types': {},
            'discovery_methods_usage': {},
            'snmp_availability': connectivity_summary['snmp_enabled']
        }
        
        discovery_results['ip_distribution'] = ip_distribution
        discovery_results['connectivity_summary'] = connectivity_summary
        
        # Analyser les types d'équipements
        for equipment_data in discovery_results['equipment_details'].values():
            eq_type = equipment_data.get('node_type', 'unknown')
            if eq_type not in discovery_results['discovery_summary']['equipment_types']:
                discovery_results['discovery_summary']['equipment_types'][eq_type] = 0
            discovery_results['discovery_summary']['equipment_types'][eq_type] += 1
        
        # Analyser l'utilisation des méthodes de découverte
        for equipment_data in discovery_results['equipment_details'].values():
            methods = equipment_data.get('discovery_methods', [])
            for method in methods:
                if method not in discovery_results['discovery_summary']['discovery_methods_usage']:
                    discovery_results['discovery_summary']['discovery_methods_usage'][method] = 0
                discovery_results['discovery_summary']['discovery_methods_usage'][method] += 1
        
        # Finaliser
        discovery_results['discovery_end_time'] = timezone.now().isoformat()
        discovery_results['discovery_duration_seconds'] = (
            timezone.now() - start_time
        ).total_seconds()
        
        logger.info(f"✅ TEST - Découverte terminée: {discovery_results['equipment_with_ips']}/{discovery_results['total_equipment']} équipements avec IPs")
        logger.info(f"🎯 TEST - Total IPs découvertes: {discovery_results['total_ips_discovered']}")
        
        return Response(discovery_results, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ TEST - Erreur découverte projet {project_id}: {e}")
        return Response({
            'test_mode': True,
            'project_id': project_id,
            'error_message': str(e),
            'discovery_end_time': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)