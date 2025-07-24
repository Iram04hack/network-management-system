"""
Module contenant les vues API pour les équipements réseau.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..application.services import DeviceService
from ..domain.exceptions import ResourceNotFoundException, ValidationException
from ..infrastructure.adapters import DjangoDeviceRepository
from .serializers import DeviceSerializer, DeviceCreateSerializer, DeviceUpdateSerializer


class DeviceViewSet(viewsets.ViewSet):
    """
    ViewSet pour les équipements réseau.
    
    Ce ViewSet fournit des endpoints pour gérer les équipements réseau.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        """
        Initialise une nouvelle instance de DeviceViewSet.
        """
        super().__init__(**kwargs)
        from ..infrastructure.repositories import DjangoNetworkInterfaceRepository
        self._service = DeviceService(
            DjangoDeviceRepository(),
            DjangoNetworkInterfaceRepository()
        )
    
    @swagger_auto_schema(
        operation_summary="Lister les équipements réseau",
        operation_description="Récupère la liste de tous les équipements réseau avec option de recherche",
        manual_parameters=[
            openapi.Parameter(
                'query',
                openapi.IN_QUERY,
                description="Terme de recherche pour filtrer les équipements",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="Liste des équipements réseau",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT)
                )
            ),
            500: openapi.Response(description="Erreur serveur")
        },
        tags=['Network Management']
    )
    def list(self, request: Request) -> Response:
        """
        Liste tous les équipements réseau.
        
        Args:
            request (Request): La requête HTTP.
            
        Returns:
            Response: La réponse HTTP contenant la liste des équipements.
        """
        try:
            # Récupérer les paramètres de requête
            query = request.query_params.get('query', '')
            
            # Récupérer les équipements
            if query:
                devices = self._service.search_devices(query)
            else:
                devices = self._service.get_all_devices()
            
            # Sérialiser les équipements
            serializer = DeviceSerializer(devices, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_summary="Récupérer un équipement",
        operation_description="Récupère les détails d'un équipement réseau spécifique",
        responses={
            200: openapi.Response(
                description="Détails de l'équipement",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT)
            ),
            404: openapi.Response(description="Équipement non trouvé"),
            500: openapi.Response(description="Erreur serveur")
        },
        tags=['Network Management']
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """
        Récupère un équipement réseau par son ID.
        
        Args:
            request (Request): La requête HTTP.
            pk: L'ID de l'équipement à récupérer.
            
        Returns:
            Response: La réponse HTTP contenant l'équipement.
        """
        try:
            # Récupérer l'équipement
            device = self._service.get_device(int(pk))
            
            # Sérialiser l'équipement
            serializer = DeviceSerializer(device)
            return Response(serializer.data)
        except ResourceNotFoundException as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_summary="Créer un équipement",
        operation_description="Crée un nouvel équipement réseau",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de l'équipement"),
                'device_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type d'équipement"),
                'ip_address': openapi.Schema(type=openapi.TYPE_STRING, description="Adresse IP"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description")
            },
            required=['name', 'device_type']
        ),
        responses={
            201: openapi.Response(
                description="Équipement créé avec succès",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT)
            ),
            400: openapi.Response(description="Données invalides"),
            500: openapi.Response(description="Erreur serveur")
        },
        tags=['Network Management']
    )
    def create(self, request: Request) -> Response:
        """
        Crée un nouvel équipement réseau.
        
        Args:
            request (Request): La requête HTTP contenant les données de l'équipement.
            
        Returns:
            Response: La réponse HTTP contenant l'équipement créé.
        """
        try:
            # Valider les données
            serializer = DeviceCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Créer l'équipement
            device = self._service.create_device(serializer.validated_data)
            
            # Sérialiser l'équipement créé
            response_serializer = DeviceSerializer(device)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_summary="Mettre à jour un équipement",
        operation_description="Met à jour complètement un équipement réseau existant",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de l'équipement"),
                'device_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type d'équipement"),
                'ip_address': openapi.Schema(type=openapi.TYPE_STRING, description="Adresse IP"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description")
            }
        ),
        responses={
            200: openapi.Response(
                description="Détails de l'équipement",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT)
            ),
            404: openapi.Response(description="Équipement non trouvé"),
            400: openapi.Response(description="Données invalides"),
            500: openapi.Response(description="Erreur serveur")
        },
        tags=['Network Management']
    )
    def update(self, request: Request, pk=None) -> Response:
        """
        Met à jour un équipement réseau existant.
        
        Args:
            request (Request): La requête HTTP contenant les nouvelles données de l'équipement.
            pk: L'ID de l'équipement à mettre à jour.
            
        Returns:
            Response: La réponse HTTP contenant l'équipement mis à jour.
        """
        try:
            # Valider les données
            serializer = DeviceUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Mettre à jour l'équipement
            device = self._service.update_device(int(pk), serializer.validated_data)
            
            # Sérialiser l'équipement mis à jour
            response_serializer = DeviceSerializer(device)
            return Response(response_serializer.data)
        except ResourceNotFoundException as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_summary="Mise à jour partielle d'un équipement",
        operation_description="Met à jour partiellement un équipement réseau existant",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de l'équipement"),
                'device_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type d'équipement"),
                'ip_address': openapi.Schema(type=openapi.TYPE_STRING, description="Adresse IP"),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description")
            }
        ),
        responses={
            200: openapi.Response(
                description="Détails de l'équipement",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT)
            ),
            404: openapi.Response(description="Équipement non trouvé"),
            400: openapi.Response(description="Données invalides"),
            500: openapi.Response(description="Erreur serveur")
        },
        tags=['Network Management']
    )
    def partial_update(self, request: Request, pk=None) -> Response:
        """
        Met à jour partiellement un équipement réseau existant.
        
        Args:
            request (Request): La requête HTTP contenant les nouvelles données de l'équipement.
            pk: L'ID de l'équipement à mettre à jour.
            
        Returns:
            Response: La réponse HTTP contenant l'équipement mis à jour.
        """
        return self.update(request, pk)
    
    @swagger_auto_schema(
        operation_summary="Supprimer un équipement",
        operation_description="Supprime définitivement un équipement réseau",
        responses={
            204: openapi.Response(description="Équipement supprimé avec succès"),
            404: openapi.Response(description="Équipement non trouvé"),
            500: openapi.Response(description="Erreur serveur")
        },
        tags=['Network Management']
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """
        Supprime un équipement réseau.
        
        Args:
            request (Request): La requête HTTP.
            pk: L'ID de l'équipement à supprimer.
            
        Returns:
            Response: La réponse HTTP indiquant le succès ou l'échec de la suppression.
        """
        try:
            # Supprimer l'équipement
            success = self._service.delete_device(int(pk))
            
            if success:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'Failed to delete device'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ResourceNotFoundException as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Interfaces d'un équipement",
        operation_description="Récupère toutes les interfaces d'un équipement réseau",
        responses={
            200: openapi.Response(description="Liste des interfaces"),
            404: openapi.Response(description="Équipement non trouvé"),
            500: openapi.Response(description="Erreur serveur")
        },
        tags=['Network Management']
    )
    @action(detail=True, methods=['get'])
    def interfaces(self, request: Request, pk=None) -> Response:
        """
        Récupère les interfaces d'un équipement réseau.
        
        Args:
            request (Request): La requête HTTP.
            pk: L'ID de l'équipement dont on veut récupérer les interfaces.
            
        Returns:
            Response: La réponse HTTP contenant les interfaces de l'équipement.
        """
        try:
            # Importer le service d'interface
            from ..application.services import InterfaceService
            from ..infrastructure.adapters import DjangoInterfaceRepository
            from .serializers import InterfaceSerializer
            
            # Créer le service d'interface
            interface_service = InterfaceService(DjangoInterfaceRepository())
            
            # Récupérer les interfaces
            interfaces = interface_service.get_interfaces_by_device(int(pk))
            
            # Sérialiser les interfaces
            serializer = InterfaceSerializer(interfaces, many=True)
            return Response(serializer.data)
        except ResourceNotFoundException as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        method='get',
        operation_summary="Configurations d'un équipement",
        operation_description="Récupère toutes les configurations d'un équipement réseau",
        responses={
            200: openapi.Response(description="Liste des configurations"),
            404: openapi.Response(description="Équipement non trouvé"),
            500: openapi.Response(description="Erreur serveur")
        },
        tags=['Network Management']
    )
    @action(detail=True, methods=['get'])
    def configurations(self, request: Request, pk=None) -> Response:
        """
        Récupère les configurations d'un équipement réseau.
        
        Args:
            request (Request): La requête HTTP.
            pk: L'ID de l'équipement dont on veut récupérer les configurations.
            
        Returns:
            Response: La réponse HTTP contenant les configurations de l'équipement.
        """
        try:
            # Importer le service de configuration
            from ..application.services import ConfigurationService
            from ..infrastructure.adapters import DjangoConfigurationRepository
            from .serializers import ConfigurationSerializer
            
            # Créer le service de configuration
            config_service = ConfigurationService(DjangoConfigurationRepository())
            
            # Récupérer les configurations
            configs = config_service.get_configurations_by_device(int(pk))
            
            # Sérialiser les configurations
            serializer = ConfigurationSerializer(configs, many=True)
            return Response(serializer.data)
        except ResourceNotFoundException as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
