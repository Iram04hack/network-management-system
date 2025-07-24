from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..di_container import qos_container
from ..application.use_cases import GetQoSRecommendationsUseCase
from ..domain.interfaces import QoSConfigurationService
from .mixins import QoSPermissionMixin, DIViewMixin, AdminRequiredMixin

from ..application.configure_cbwfq_use_case import (
    ConfigureCBWFQUseCase,
    CalculateBandwidthAllocationUseCase
)
from ..domain.exceptions import (
    QoSConfigurationException,
    QoSValidationException,
    NetworkDeviceNotFoundException
)

logger = logging.getLogger(__name__)

class QoSConfigurerView(QoSPermissionMixin, APIView):
    """
    Assistant intelligent de configuration QoS automatique.
    
    Génère des recommandations de configuration QoS optimisées selon :
    - Le type de trafic principal (VoIP, vidéo, données, gaming)
    - La taille et topologie du réseau
    - Les contraintes de bande passante
    - Les bonnes pratiques par industrie
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialiser les dépendances via le conteneur
        from ..di_container import resolve
        from ..application.use_cases import GetQoSRecommendationsUseCase
        self.get_recommendations_use_case = resolve(GetQoSRecommendationsUseCase)
    
    @swagger_auto_schema(
        operation_summary="Recommandations QoS intelligentes",
        operation_description="""
        Génère automatiquement des recommandations de configuration QoS optimisées.
        
        **L'assistant analyse :**
        - Le type de trafic principal de votre réseau
        - La taille et complexité de l'infrastructure  
        - Les contraintes de bande passante disponible
        - Les bonnes pratiques de l'industrie
        
        **Types de trafic supportés :**
        - `general` : Configuration équilibrée pour usage mixte
        - `voip` : Optimisation pour VoIP avec latence minimale
        - `video` : Priorité aux flux vidéo et streaming
        - `gaming` : Configuration gaming avec faible latence
        - `data` : Optimisation pour transferts de données
        
        **Tailles de réseau :**
        - `small` : < 50 utilisateurs
        - `medium` : 50-500 utilisateurs  
        - `large` : > 500 utilisateurs
        """,
        manual_parameters=[
            openapi.Parameter('type', openapi.IN_QUERY, description="Type de trafic principal", type=openapi.TYPE_STRING, enum=['general', 'voip', 'video', 'gaming', 'data']),
            openapi.Parameter('size', openapi.IN_QUERY, description="Taille du réseau", type=openapi.TYPE_STRING, enum=['small', 'medium', 'large']),
        ],
        responses={
            200: openapi.Response("Recommandations QoS générées", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'policy_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de la politique recommandée"),
                    'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description de la configuration"),
                    'traffic_classes': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'priority': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'min_bandwidth': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'max_bandwidth': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'dscp': openapi.Schema(type=openapi.TYPE_INTEGER)
                            }
                        )
                    )
                }
            )),
            500: "Erreur serveur interne"
        },
        tags=['QoS Management']
    )
    def get(self, request):
        """Obtenir les configurations QoS recommandées"""
        traffic_type = request.query_params.get('type', 'general')
        network_size = request.query_params.get('size', 'medium')
        
        try:
            # Exécuter le cas d'utilisation
            recommendations = self.get_recommendations_use_case.execute(
                traffic_type=traffic_type,
                network_size=network_size
            )
            
            # Convertir l'objet de domaine en dictionnaire pour la réponse
            result = {
                'policy_name': recommendations.policy_name,
                'description': recommendations.description,
                'traffic_classes': [
                    {
                        'name': tc.name,
                        'description': tc.description,
                        'dscp': tc.dscp,
                        'priority': tc.priority,
                        'min_bandwidth': tc.min_bandwidth,
                        'max_bandwidth': tc.max_bandwidth
                    }
                    for tc in recommendations.traffic_classes
                ]
            }
            
            return Response(result)
        except Exception as e:
            logger.exception(f"Erreur lors de la génération des recommandations QoS: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CBWFQConfigView(DIViewMixin, QoSPermissionMixin, AdminRequiredMixin, APIView):
    """
    Vue pour configurer CBWFQ sur un appareil réseau.
    
    Configuration avancée de Class-Based Weighted Fair Queueing :
    - Application de CBWFQ sur interfaces spécifiques
    - Génération automatique de commandes d'équipement
    - Validation des paramètres de configuration
    - Support multi-constructeur (Cisco, Juniper, Linux)
    """
    
    # Configurer les dépendances requises
    _dependencies = {
        "configure_cbwfq_use_case": ConfigureCBWFQUseCase
    }
    
    permission_type = "qos_configuration"
    
    @swagger_auto_schema(
        operation_summary="Configurer CBWFQ sur un équipement",
        operation_description="""
        Configure l'algorithme Class-Based Weighted Fair Queueing sur une interface d'équipement réseau.
        
        **Fonctionnalités :**
        - Génération automatique de commandes spécifiques à l'équipement
        - Configuration des files d'attente par classe de trafic
        - Application des poids et priorités CBWFQ
        - Validation de la compatibilité matérielle
        
        **Paramètres requis :**
        - `device_id` : ID de l'équipement cible
        - `interface_name` : Nom de l'interface (ex: GigabitEthernet0/1)
        - `direction` : Direction du trafic (ingress/egress)
        
        **Constructeurs supportés :**
        - Cisco IOS/IOS-XE (class-map, policy-map)
        - Juniper Junos (scheduler-map, forwarding-class)
        - Linux TC (qdisc, class)
        """,
        manual_parameters=[
            openapi.Parameter('policy_id', openapi.IN_PATH, description="ID de la politique QoS", type=openapi.TYPE_INTEGER, required=True),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'device_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'équipement"),
                'interface_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de l'interface"),
                'direction': openapi.Schema(type=openapi.TYPE_STRING, description="Direction du trafic", enum=['ingress', 'egress'])
            },
            required=['device_id', 'interface_name']
        ),
        responses={
            200: openapi.Response("Configuration CBWFQ appliquée", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Statut de la configuration"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message de confirmation"),
                    'interface': openapi.Schema(type=openapi.TYPE_STRING, description="Interface configurée"),
                    'policy_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la politique"),
                    'device_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'équipement"),
                    'queue_configurations': openapi.Schema(type=openapi.TYPE_INTEGER, description="Nombre de files configurées"),
                    'commands': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="Commandes générées")
                }
            )),
            400: "Paramètres invalides ou échec de validation",
            404: "Politique, équipement ou interface non trouvée",
            500: "Erreur lors de la configuration CBWFQ"
        },
        tags=['QoS Management']
    )
    def post(self, request, policy_id):
        """
        Configure CBWFQ sur une interface d'un appareil réseau.
        """
        try:
            device_id = request.data.get('device_id')
            interface_name = request.data.get('interface_name')
            direction = request.data.get('direction', 'egress')
            
            if not device_id or not interface_name:
                return Response(
                    {"detail": "Les champs 'device_id' et 'interface_name' sont obligatoires"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = self.configure_cbwfq_use_case.execute(
                int(policy_id),
                int(device_id),
                interface_name,
                direction
            )
            
            return Response({
                "success": result.success,
                "message": result.message,
                "interface": interface_name,
                "policy_id": policy_id,
                "device_id": device_id,
                "direction": direction,
                "queue_configurations": len(result.queue_configurations),
                "commands": result.commands_generated or []
            })
            
        except QoSValidationException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except QoSConfigurationException as e:
            return Response(
                {"detail": str(e), "reason": e.reason},
                status=status.HTTP_400_BAD_REQUEST
            )
        except NetworkDeviceNotFoundException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception(f"Erreur lors de la configuration CBWFQ: {str(e)}")
            return Response(
                {"detail": f"Une erreur s'est produite: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BandwidthAllocationView(DIViewMixin, QoSPermissionMixin, APIView):
    """
    Vue pour calculer l'allocation de bande passante selon CBWFQ.
    
    Calcul et visualisation des allocations de bande passante :
    - Répartition optimale selon l'algorithme CBWFQ
    - Calcul des poids par classe de trafic
    - Estimation des débits garantis et maximum
    - Analyse de l'efficacité de l'allocation
    """
    
    # Configurer les dépendances requises
    _dependencies = {
        "calculate_bandwidth_allocation_use_case": CalculateBandwidthAllocationUseCase
    }
    
    permission_type = "qos_view"
    
    @swagger_auto_schema(
        operation_summary="Calculer l'allocation de bande passante CBWFQ",
        operation_description="""
        Calcule l'allocation optimale de bande passante selon l'algorithme CBWFQ.
        
        **Calculs effectués :**
        - Répartition proportionnelle selon les poids des classes
        - Débits garantis minimums par classe
        - Débits maximum autorisés
        - Bande passante restante disponible
        
        **Algorithme CBWFQ :**
        - Allocation basée sur les pourcentages de bande passante
        - Respect des priorités et garanties minimums
        - Gestion de la bande passante excédentaire
        - Optimisation pour réduire la latence
        
        **Informations retournées :**
        - Allocation détaillée par classe de trafic
        - Pourcentages calculés et débits en kbps
        - Statistiques d'efficacité de l'allocation
        - Recommandations d'optimisation
        """,
        manual_parameters=[
            openapi.Parameter('policy_id', openapi.IN_PATH, description="ID de la politique QoS", type=openapi.TYPE_INTEGER, required=True),
        ],
        responses={
            200: openapi.Response("Allocation de bande passante calculée", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'policy_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la politique"),
                    'allocations': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'class_name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de la classe"),
                                'bandwidth_percent': openapi.Schema(type=openapi.TYPE_NUMBER, description="Pourcentage alloué"),
                                'guaranteed_rate_kbps': openapi.Schema(type=openapi.TYPE_INTEGER, description="Débit garanti (kbps)"),
                                'max_rate_kbps': openapi.Schema(type=openapi.TYPE_INTEGER, description="Débit maximum (kbps)"),
                                'priority': openapi.Schema(type=openapi.TYPE_INTEGER, description="Niveau de priorité")
                            }
                        )
                    ),
                    'total_classes': openapi.Schema(type=openapi.TYPE_INTEGER, description="Nombre total de classes")
                }
            )),
            400: "Politique invalide ou erreur de calcul",
            404: "Politique QoS non trouvée",
            500: "Erreur lors du calcul d'allocation"
        },
        tags=['QoS Management']
    )
    def get(self, request, policy_id):
        """
        Calcule l'allocation de bande passante pour une politique QoS selon CBWFQ.
        """
        try:
            allocations = self.calculate_bandwidth_allocation_use_case.execute(int(policy_id))
            
            return Response({
                "policy_id": policy_id,
                "allocations": allocations,
                "total_classes": len(allocations)
            })
            
        except QoSValidationException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception(f"Erreur lors du calcul d'allocation de bande passante: {str(e)}")
            return Response(
                {"detail": f"Une erreur s'est produite: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 