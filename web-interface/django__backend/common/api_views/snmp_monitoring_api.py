"""
API avancée pour le monitoring SNMP en temps réel des équipements GNS3.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
import asyncio
import threading
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

from api_clients.network.snmp_client import SNMPClient, SNMPCredentials, SNMPVersion

@dataclass
class SNMPMonitoringSession:
    """Session de monitoring SNMP."""
    session_id: str
    device_ip: str
    community: str
    interval: int
    metrics: List[str]
    active: bool = True
    start_time: Optional[str] = None
    last_collection: Optional[str] = None
    total_collections: int = 0
    error_count: int = 0

class SNMPMonitoringService:
    """Service de monitoring SNMP avancé."""
    
    def __init__(self):
        pass  # SNMPClient sera créé à la demande
        self.active_sessions: Dict[str, SNMPMonitoringSession] = {}
        self.monitoring_data: Dict[str, List[Dict]] = {}
        self.monitoring_threads: Dict[str, threading.Thread] = {}
        
    def start_monitoring_session(self, session_config: Dict[str, Any]) -> str:
        """Démarre une session de monitoring SNMP."""
        import uuid
        session_id = str(uuid.uuid4())
        
        session = SNMPMonitoringSession(
            session_id=session_id,
            device_ip=session_config['device_ip'],
            community=session_config.get('community', 'public'),
            interval=session_config.get('interval', 30),
            metrics=session_config.get('metrics', ['system', 'interfaces', 'performance']),
            start_time=timezone.now().isoformat()
        )
        
        self.active_sessions[session_id] = session
        self.monitoring_data[session_id] = []
        
        # Démarrer le thread de monitoring
        thread = threading.Thread(
            target=self._monitoring_loop,
            args=(session_id,),
            daemon=True
        )
        thread.start()
        self.monitoring_threads[session_id] = thread
        
        return session_id
        
    def stop_monitoring_session(self, session_id: str) -> bool:
        """Arrête une session de monitoring."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].active = False
            
            # Attendre un peu pour que le thread se termine
            if session_id in self.monitoring_threads:
                thread = self.monitoring_threads[session_id]
                thread.join(timeout=2)
                del self.monitoring_threads[session_id]
                
            return True
        return False
        
    def get_session_data(self, session_id: str, limit: int = 100) -> List[Dict]:
        """Récupère les données d'une session."""
        if session_id in self.monitoring_data:
            return self.monitoring_data[session_id][-limit:]
        return []
        
    def _monitoring_loop(self, session_id: str):
        """Boucle de monitoring pour une session."""
        session = self.active_sessions[session_id]
        
        while session.active:
            try:
                collection_time = timezone.now()
                
                # Collecter les métriques demandées
                collected_data = {
                    'session_id': session_id,
                    'timestamp': collection_time.isoformat(),
                    'device_ip': session.device_ip,
                    'metrics': {}
                }
                
                # Créer le client SNMP pour cette IP
                credentials = SNMPCredentials(version=SNMPVersion.V2C, community=session.community)
                snmp_client = SNMPClient(session.device_ip, credentials=credentials)
                
                # Collecte selon les métriques demandées
                if 'system' in session.metrics:
                    system_data = snmp_client.get_system_info()
                    collected_data['metrics']['system'] = system_data
                    
                if 'interfaces' in session.metrics:
                    interfaces_data = snmp_client.get_interfaces_info()
                    collected_data['metrics']['interfaces'] = interfaces_data
                    
                if 'performance' in session.metrics:
                    performance_data = snmp_client.get_performance_metrics()
                    collected_data['metrics']['performance'] = performance_data
                    
                # Stocker les données
                self.monitoring_data[session_id].append(collected_data)
                
                # Limiter la taille des données stockées (garder les 1000 dernières)
                if len(self.monitoring_data[session_id]) > 1000:
                    self.monitoring_data[session_id] = self.monitoring_data[session_id][-1000:]
                    
                # Mettre à jour les statistiques de session
                session.last_collection = collection_time.isoformat()
                session.total_collections += 1
                
            except Exception as e:
                session.error_count += 1
                error_data = {
                    'session_id': session_id,
                    'timestamp': timezone.now().isoformat(),
                    'error': str(e),
                    'device_ip': session.device_ip
                }
                self.monitoring_data[session_id].append(error_data)
                
            # Attendre l'intervalle suivant
            time.sleep(session.interval)
            
    def get_all_sessions(self) -> List[Dict]:
        """Retourne toutes les sessions actives."""
        sessions = []
        for session in self.active_sessions.values():
            sessions.append({
                'session_id': session.session_id,
                'device_ip': session.device_ip,
                'community': session.community,
                'interval': session.interval,
                'metrics': session.metrics,
                'active': session.active,
                'start_time': session.start_time,
                'last_collection': session.last_collection,
                'total_collections': session.total_collections,
                'error_count': session.error_count
            })
        return sessions

# Instance globale du service
snmp_monitoring_service = SNMPMonitoringService()

@swagger_auto_schema(
    method='post',
    operation_description="Démarre une session de monitoring SNMP en temps réel",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['device_ip'],
        properties={
            'device_ip': openapi.Schema(type=openapi.TYPE_STRING, description="Adresse IP de l'équipement"),
            'community': openapi.Schema(type=openapi.TYPE_STRING, description="Communauté SNMP", default='public'),
            'interval': openapi.Schema(type=openapi.TYPE_INTEGER, description="Intervalle en secondes", default=30),
            'metrics': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                description="Métriques à collecter",
                default=['system', 'interfaces', 'performance']
            ),
        }
    ),
    responses={
        200: openapi.Response(
            description="Session de monitoring créée",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'session_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'device_ip': openapi.Schema(type=openapi.TYPE_STRING),
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'start_time': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def start_snmp_monitoring(request):
    """
    Démarre une session de monitoring SNMP en temps réel.
    
    Lance la collecte continue de métriques SNMP pour un équipement.
    """
    try:
        session_config = {
            'device_ip': request.data.get('device_ip'),
            'community': request.data.get('community', 'public'),
            'interval': request.data.get('interval', 30),
            'metrics': request.data.get('metrics', ['system', 'interfaces', 'performance'])
        }
        
        if not session_config['device_ip']:
            return Response(
                {'error': 'device_ip est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Valider l'intervalle
        if session_config['interval'] < 5:
            return Response(
                {'error': 'L\'intervalle minimum est de 5 secondes'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        session_id = snmp_monitoring_service.start_monitoring_session(session_config)
        
        return Response({
            'session_id': session_id,
            'device_ip': session_config['device_ip'],
            'status': 'started',
            'start_time': timezone.now().isoformat(),
            'interval': session_config['interval'],
            'metrics': session_config['metrics']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du démarrage du monitoring: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='delete',
    operation_description="Arrête une session de monitoring SNMP",
    manual_parameters=[
        openapi.Parameter('session_id', openapi.IN_PATH, description="ID de la session", type=openapi.TYPE_STRING, required=True),
    ],
    responses={
        200: openapi.Response(description="Session arrêtée"),
        404: openapi.Response(description="Session non trouvée")
    },
    tags=['Common - Infrastructure']
)
@api_view(['DELETE'])
@permission_classes([])
def stop_snmp_monitoring(request, session_id):
    """
    Arrête une session de monitoring SNMP.
    
    Termine la collecte continue pour la session spécifiée.
    """
    try:
        success = snmp_monitoring_service.stop_monitoring_session(session_id)
        
        if success:
            return Response({
                'session_id': session_id,
                'status': 'stopped',
                'stop_time': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Session non trouvée'},
                status=status.HTTP_404_NOT_FOUND
            )
            
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de l\'arrêt du monitoring: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Récupère les données d'une session de monitoring",
    manual_parameters=[
        openapi.Parameter('session_id', openapi.IN_PATH, description="ID de la session", type=openapi.TYPE_STRING, required=True),
        openapi.Parameter('limit', openapi.IN_QUERY, description="Nombre max d'enregistrements", type=openapi.TYPE_INTEGER, default=100),
        openapi.Parameter('from_timestamp', openapi.IN_QUERY, description="Timestamp de début", type=openapi.TYPE_STRING),
    ],
    responses={
        200: openapi.Response(
            description="Données de monitoring",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'session_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'data_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'monitoring_data': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def get_snmp_monitoring_data(request, session_id):
    """
    Récupère les données collectées d'une session de monitoring.
    
    Retourne les métriques SNMP collectées avec possibilité de filtrage.
    """
    try:
        limit = int(request.GET.get('limit', 100))
        from_timestamp = request.GET.get('from_timestamp')
        
        data = snmp_monitoring_service.get_session_data(session_id, limit)
        
        # Filtrer par timestamp si fourni
        if from_timestamp:
            filtered_data = []
            for item in data:
                if item.get('timestamp', '') >= from_timestamp:
                    filtered_data.append(item)
            data = filtered_data
            
        return Response({
            'session_id': session_id,
            'data_count': len(data),
            'monitoring_data': data,
            'retrieved_at': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des données: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='get',
    operation_description="Liste toutes les sessions de monitoring SNMP actives",
    responses={
        200: openapi.Response(
            description="Liste des sessions",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'active_sessions': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'sessions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['GET'])
@permission_classes([])
def list_snmp_monitoring_sessions(request):
    """
    Liste toutes les sessions de monitoring SNMP actives.
    
    Retourne un aperçu de toutes les sessions de monitoring en cours.
    """
    try:
        sessions = snmp_monitoring_service.get_all_sessions()
        
        return Response({
            'active_sessions': len(sessions),
            'sessions': sessions,
            'retrieved_at': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors de la récupération des sessions: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@swagger_auto_schema(
    method='post',
    operation_description="Test SNMP rapide pour un équipement",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['device_ip'],
        properties={
            'device_ip': openapi.Schema(type=openapi.TYPE_STRING),
            'community': openapi.Schema(type=openapi.TYPE_STRING, default='public'),
            'test_types': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_STRING),
                default=['connectivity', 'system', 'interfaces']
            ),
        }
    ),
    responses={
        200: openapi.Response(
            description="Résultats du test SNMP",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'device_ip': openapi.Schema(type=openapi.TYPE_STRING),
                    'snmp_available': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'test_results': openapi.Schema(type=openapi.TYPE_OBJECT),
                    'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                }
            )
        )
    },
    tags=['Common - Infrastructure']
)
@api_view(['POST'])
@permission_classes([])
def test_snmp_connectivity(request):
    """
    Test SNMP rapide pour vérifier la connectivité et les capacités.
    
    Effectue des tests SNMP pour déterminer les capacités de monitoring.
    """
    try:
        device_ip = request.data.get('device_ip')
        community = request.data.get('community', 'public')
        test_types = request.data.get('test_types', ['connectivity', 'system', 'interfaces'])
        
        if not device_ip:
            return Response(
                {'error': 'device_ip est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        credentials = SNMPCredentials(version=SNMPVersion.V2C, community=community)
        snmp_client = SNMPClient(device_ip, credentials=credentials)
        
        test_results = {
            'device_ip': device_ip,
            'community': community,
            'test_timestamp': timezone.now().isoformat(),
            'snmp_available': False,
            'test_results': {},
            'recommendations': []
        }
        
        # Test de connectivité de base
        if 'connectivity' in test_types:
            try:
                # Test simple avec sysName
                result = snmp_client.get_system_info()
                if result['success']:
                    test_results['snmp_available'] = True
                    test_results['test_results']['connectivity'] = {
                        'status': 'success',
                        'response_time_ms': result.get('response_time_ms'),
                        'snmp_version': '2c'  # Version utilisée par défaut
                    }
                else:
                    test_results['test_results']['connectivity'] = {
                        'status': 'failed',
                        'error': result.get('error')
                    }
            except Exception as e:
                test_results['test_results']['connectivity'] = {
                    'status': 'error',
                    'error': str(e)
                }
                
        # Test des informations système
        if 'system' in test_types and test_results['snmp_available']:
            try:
                system_result = snmp_client.get_system_info()
                test_results['test_results']['system'] = system_result
            except Exception as e:
                test_results['test_results']['system'] = {'error': str(e)}
                
        # Test des interfaces
        if 'interfaces' in test_types and test_results['snmp_available']:
            try:
                interfaces_result = snmp_client.get_interfaces_info()
                test_results['test_results']['interfaces'] = interfaces_result
            except Exception as e:
                test_results['test_results']['interfaces'] = {'error': str(e)}
                
        # Générer des recommandations
        if test_results['snmp_available']:
            test_results['recommendations'].append("SNMP est disponible - monitoring recommandé")
            
            # Analyser les capacités
            system_info = test_results['test_results'].get('system', {})
            if system_info.get('success'):
                test_results['recommendations'].append("Informations système disponibles")
                
            interfaces_info = test_results['test_results'].get('interfaces', {})
            if interfaces_info.get('success'):
                interface_count = len(interfaces_info.get('interfaces', {}))
                test_results['recommendations'].append(f"{interface_count} interfaces détectées")
                
        else:
            test_results['recommendations'].extend([
                "SNMP non disponible avec la communauté 'public'",
                "Essayez d'autres communautés: private, cisco, admin",
                "Vérifiez que SNMP est activé sur l'équipement",
                "Vérifiez les règles de pare-feu (port 161 UDP)"
            ])
            
        return Response(test_results, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Erreur lors du test SNMP: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )