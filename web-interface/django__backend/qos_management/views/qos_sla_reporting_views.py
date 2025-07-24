"""
Vues pour les rapports de conformité SLA et les performances QoS.

Ce module fournit les vues pour générer et analyser les rapports
de conformité SLA et les performances QoS.
"""

import logging
from datetime import datetime
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..di_container import qos_container
from ..application.sla_compliance_use_cases import (
    GetSLAComplianceReportUseCase,
    GetQoSPerformanceReportUseCase,
    AnalyzeSLATrendsUseCase
)
from ..domain.exceptions import QoSMonitoringException

logger = logging.getLogger(__name__)


class SLAComplianceReportView(APIView):
    """
    Vue pour les rapports de conformité SLA.
    
    Génération de rapports de conformité SLA détaillés :
    - Analyse de conformité par équipement
    - Métriques de performance temps réel
    - Calcul des taux de respect des SLA
    - Identification des violations et tendances
    """
    
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Rapport de conformité SLA",
        operation_description="""
        Génère un rapport détaillé de conformité SLA pour un équipement spécifique.
        
        **Métriques analysées :**
        - Respect des seuils de latence
        - Taux de perte de paquets
        - Disponibilité de bande passante
        - Temps de réponse des services
        - Conformité aux accords de niveau de service
        
        **Périodes supportées :**
        - `1h` : Dernière heure
        - `24h` : Dernières 24 heures (défaut)
        - `7d` : Dernière semaine
        - `30d` : Dernier mois
        
        **Format de rapport :**
        - Scores de conformité globaux
        - Détail des violations par métrique
        - Tendances et recommandations
        """,
        manual_parameters=[
            openapi.Parameter('device_id', openapi.IN_PATH, description="ID de l'équipement", type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('period', openapi.IN_QUERY, description="Période d'analyse", type=openapi.TYPE_STRING, enum=['1h', '24h', '7d', '30d']),
        ],
        responses={
            200: openapi.Response("Rapport de conformité SLA", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'device_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'équipement"),
                    'period': openapi.Schema(type=openapi.TYPE_STRING, description="Période analysée"),
                    'overall_compliance': openapi.Schema(type=openapi.TYPE_NUMBER, description="Taux de conformité global (%)"),
                    'metrics': openapi.Schema(type=openapi.TYPE_OBJECT, description="Détail des métriques"),
                    'violations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="Liste des violations")
                }
            )),
            400: "Paramètres invalides ou équipement non monitored",
            404: "Équipement non trouvé",
            500: "Erreur lors de la génération du rapport"
        },
        tags=['QoS Management']
    )
    def get(self, request, device_id, format=None):
        """
        Récupère un rapport de conformité SLA pour un équipement.
        
        Args:
            request: Requête HTTP
            device_id: ID de l'équipement
            format: Format de sortie (optionnel)
            
        Returns:
            Response: Rapport de conformité SLA
        """
        try:
            # Récupérer les paramètres
            period = request.query_params.get('period', '24h')
            
            # Récupérer le conteneur et résoudre le cas d'utilisation
            container = get_container()
            use_case = container.resolve(GetSLAComplianceReportUseCase)
            
            # Exécuter le cas d'utilisation
            result = use_case.execute(int(device_id), period)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except QoSMonitoringException as e:
            logger.error(f"Erreur lors de la génération du rapport SLA: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la génération du rapport SLA: {str(e)}")
            return Response({
                'success': False,
                'error': f"Erreur serveur: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QoSPerformanceReportView(APIView):
    """
    Vue pour les rapports de performance QoS.
    
    Génération de rapports de performance QoS globaux :
    - Analyse des performances multi-équipements
    - Métriques d'efficacité des politiques QoS
    - Comparaison des performances par classe de trafic
    - Identification des goulots d'étranglement
    """
    
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Rapport de performance QoS global",
        operation_description="""
        Génère un rapport de performance QoS global pour l'infrastructure.
        
        **Analyses incluses :**
        - Performance par politique QoS
        - Efficacité des algorithmes de queueing
        - Utilisation optimale de la bande passante
        - Impact des classifications de trafic
        - Recommandations d'optimisation
        
        **Filtrage par équipements :**
        - Analyse globale (par défaut)
        - Analyse sélective par liste d'équipements
        - Comparaison inter-équipements
        
        **Métriques de performance :**
        - Latence moyenne par classe
        - Taux d'utilisation de bande passante
        - Efficacité des files d'attente
        - Conformité aux allocations prévues
        """,
        manual_parameters=[
            openapi.Parameter('period', openapi.IN_QUERY, description="Période d'analyse", type=openapi.TYPE_STRING, enum=['1h', '24h', '7d', '30d']),
            openapi.Parameter('device_ids', openapi.IN_QUERY, description="IDs des équipements (séparés par virgules)", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response("Rapport de performance QoS", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'period': openapi.Schema(type=openapi.TYPE_STRING, description="Période analysée"),
                    'devices_analyzed': openapi.Schema(type=openapi.TYPE_INTEGER, description="Nombre d'équipements analysés"),
                    'overall_performance': openapi.Schema(type=openapi.TYPE_OBJECT, description="Performance globale"),
                    'policy_efficiency': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="Efficacité par politique"),
                    'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="Recommandations d'optimisation")
                }
            )),
            400: "Paramètres invalides ou format device_ids incorrect",
            500: "Erreur lors de la génération du rapport"
        },
        tags=['QoS Management']
    )
    def get(self, request, format=None):
        """
        Récupère un rapport de performance QoS global.
        
        Args:
            request: Requête HTTP
            format: Format de sortie (optionnel)
            
        Returns:
            Response: Rapport de performance QoS
        """
        try:
            # Récupérer les paramètres
            period = request.query_params.get('period', '7d')
            device_ids_param = request.query_params.get('device_ids')
            
            device_ids = None
            if device_ids_param:
                try:
                    device_ids = [int(id.strip()) for id in device_ids_param.split(',')]
                except ValueError:
                    return Response({
                        'success': False,
                        'error': "Format invalide pour device_ids. Utiliser une liste d'IDs séparés par des virgules."
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer le conteneur et résoudre le cas d'utilisation
            container = get_container()
            use_case = container.resolve(GetQoSPerformanceReportUseCase)
            
            # Exécuter le cas d'utilisation
            result = use_case.execute(device_ids, period)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except QoSMonitoringException as e:
            logger.error(f"Erreur lors de la génération du rapport QoS: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la génération du rapport QoS: {str(e)}")
            return Response({
                'success': False,
                'error': f"Erreur serveur: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class SLATrendAnalysisView(APIView):
    """
    Vue pour l'analyse des tendances SLA.
    
    Analyse approfondie des tendances de conformité SLA :
    - Évolution temporelle des métriques
    - Identification des patterns et cycles
    - Prédiction des risques de non-conformité
    - Analyse comparative par périodes
    """
    
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Analyse des tendances SLA",
        operation_description="""
        Analyse les tendances de conformité SLA sur une période personnalisée.
        
        **Analyses temporelles :**
        - Évolution des métriques de performance
        - Identification des périodes critiques
        - Corrélation entre différentes métriques
        - Détection des anomalies et patterns
        
        **Intervalles d'agrégation :**
        - `1h` : Agrégation horaire
        - `1d` : Agrégation quotidienne (défaut)
        - `1w` : Agrégation hebdomadaire
        
        **Visualisations incluses :**
        - Graphiques de tendance temporelle
        - Histogrammes de distribution
        - Cartes de chaleur des violations
        - Indicateurs de seuils critiques
        """,
        manual_parameters=[
            openapi.Parameter('device_id', openapi.IN_PATH, description="ID de l'équipement", type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Date de début (YYYY-MM-DD)", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="Date de fin (YYYY-MM-DD)", type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('interval', openapi.IN_QUERY, description="Intervalle d'agrégation", type=openapi.TYPE_STRING, enum=['1h', '1d', '1w']),
        ],
        responses={
            200: openapi.Response("Analyse des tendances SLA", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'device_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'équipement"),
                    'analysis_period': openapi.Schema(type=openapi.TYPE_OBJECT, description="Période d'analyse"),
                    'trends': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="Données de tendance"),
                    'anomalies': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="Anomalies détectées"),
                    'predictions': openapi.Schema(type=openapi.TYPE_OBJECT, description="Prédictions basées sur les tendances")
                }
            )),
            400: "Paramètres manquants ou dates invalides",
            404: "Équipement non trouvé",
            500: "Erreur lors de l'analyse des tendances"
        },
        tags=['QoS Management']
    )
    def get(self, request, device_id, format=None):
        """
        Analyse les tendances SLA sur une période donnée.
        
        Args:
            request: Requête HTTP
            device_id: ID de l'équipement
            format: Format de sortie (optionnel)
            
        Returns:
            Response: Analyse des tendances SLA
        """
        try:
            # Récupérer les paramètres
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            interval = request.query_params.get('interval', '1d')
            
            # Vérifier les paramètres obligatoires
            if not start_date or not end_date:
                return Response({
                    'success': False,
                    'error': "Les paramètres start_date et end_date sont obligatoires."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer le conteneur et résoudre le cas d'utilisation
            container = get_container()
            use_case = container.resolve(AnalyzeSLATrendsUseCase)
            
            # Exécuter le cas d'utilisation
            result = use_case.execute(int(device_id), start_date, end_date, interval)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except QoSMonitoringException as e:
            logger.error(f"Erreur lors de l'analyse des tendances SLA: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'analyse des tendances SLA: {str(e)}")
            return Response({
                'success': False,
                'error': f"Erreur serveur: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 