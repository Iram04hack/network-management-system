"""
Module contenant les vues API pour les interfaces réseau.
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..application.services import InterfaceService
from ..domain.exceptions import NetworkInterfaceNotFoundException, ValidationException
from ..infrastructure.adapters import DjangoInterfaceRepository
from .serializers import InterfaceSerializer, InterfaceCreateSerializer, InterfaceUpdateSerializer


class InterfaceViewSet(viewsets.ViewSet):
    """ViewSet pour les interfaces réseau."""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        """
        Initialise une nouvelle instance de InterfaceViewSet.
        """
        super().__init__(**kwargs)
        self._service = InterfaceService(DjangoInterfaceRepository())
    
    @swagger_auto_schema(
        operation_summary="Liste des interfaces réseau",
        operation_description="Récupère la liste des interfaces réseau avec filtrage optionnel",
        responses={
            200: openapi.Response("Liste des interfaces", InterfaceSerializer(many=True)),
            500: "Erreur serveur"
        },
        tags=['Network Management']
    )
    def list(self, request: Request) -> Response:
        """
        Liste toutes les interfaces réseau.
        
        Args:
            request (Request): La requête HTTP.
            
        Returns:
            Response: La réponse HTTP contenant la liste des interfaces.
        """
        try:
            # Récupérer les paramètres de requête
            query = request.query_params.get('query', '')
            device_id = request.query_params.get('device_id')
            
            # Récupérer les interfaces
            if device_id:
                interfaces = self._service.get_interfaces_by_device(int(device_id))
            elif query:
                interfaces = self._service.search_interfaces(query)
            else:
                # Pour éviter de récupérer toutes les interfaces (potentiellement nombreuses),
                # on demande un filtre
                return Response(
                    {'error': 'Please provide a query or device_id parameter'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Sérialiser les interfaces
            serializer = InterfaceSerializer(interfaces, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_summary="Détails d'une interface réseau",
        operation_description="Récupère les détails d'une interface réseau spécifique",
        responses={
            200: openapi.Response("Interface trouvée", InterfaceSerializer),
            404: "Interface non trouvée"
        },
        tags=['Network Management']
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """
        Récupère une interface réseau par son ID.
        
        Args:
            request (Request): La requête HTTP.
            pk: L'ID de l'interface à récupérer.
            
        Returns:
            Response: La réponse HTTP contenant l'interface.
        """
        try:
            # Récupérer l'interface
            interface = self._service.get_interface(int(pk))
            
            # Sérialiser l'interface
            serializer = InterfaceSerializer(interface)
            return Response(serializer.data)
        except NetworkInterfaceNotFoundException as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @swagger_auto_schema(
        operation_summary="Créer une interface réseau",
        operation_description="Crée une nouvelle interface réseau",
        request_body=InterfaceCreateSerializer,
        responses={
            201: openapi.Response("Interface créée", InterfaceSerializer),
            400: "Données invalides"
        },
        tags=['Network Management']
    )
    def create(self, request: Request) -> Response:
        """
        Crée une nouvelle interface réseau.
        
        Args:
            request (Request): La requête HTTP contenant les données de l'interface.
            
        Returns:
            Response: La réponse HTTP contenant l'interface créée.
        """
        try:
            # Valider les données
            serializer = InterfaceCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Préparer les données pour le service
            interface_data = serializer.validated_data.copy()
            
            # Récupérer l'équipement associé
            from ..domain.entities import NetworkDevice
            from ..application.services import DeviceService
            from ..infrastructure.adapters import DjangoDeviceRepository
            
            device_service = DeviceService(DjangoDeviceRepository())
            device = device_service.get_device(interface_data.pop('device_id'))
            interface_data['device'] = device
            
            # Créer l'interface
            interface = self._service.create_interface(interface_data)
            
            # Sérialiser l'interface créée
            response_serializer = InterfaceSerializer(interface)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except NetworkInterfaceNotFoundException as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request: Request, pk=None) -> Response:
        """
        Met à jour une interface réseau existante.
        
        Args:
            request (Request): La requête HTTP contenant les nouvelles données de l'interface.
            pk: L'ID de l'interface à mettre à jour.
            
        Returns:
            Response: La réponse HTTP contenant l'interface mise à jour.
        """
        try:
            # Valider les données
            serializer = InterfaceUpdateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Mettre à jour l'interface
            interface = self._service.update_interface(int(pk), serializer.validated_data)
            
            # Sérialiser l'interface mise à jour
            response_serializer = InterfaceSerializer(interface)
            return Response(response_serializer.data)
        except NetworkInterfaceNotFoundException as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValidationException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def partial_update(self, request: Request, pk=None) -> Response:
        """
        Met à jour partiellement une interface réseau existante.
        
        Args:
            request (Request): La requête HTTP contenant les nouvelles données de l'interface.
            pk: L'ID de l'interface à mettre à jour.
            
        Returns:
            Response: La réponse HTTP contenant l'interface mise à jour.
        """
        return self.update(request, pk)
    
    def destroy(self, request: Request, pk=None) -> Response:
        """
        Supprime une interface réseau.
        
        Args:
            request (Request): La requête HTTP.
            pk: L'ID de l'interface à supprimer.
            
        Returns:
            Response: La réponse HTTP indiquant le succès ou l'échec de la suppression.
        """
        try:
            # Supprimer l'interface
            success = self._service.delete_interface(int(pk))
            
            if success:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'Failed to delete interface'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except NetworkInterfaceNotFoundException as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 