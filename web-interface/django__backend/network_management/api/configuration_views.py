"""
Module contenant les vues API pour les configurations d'équipements.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..application.services import ConfigurationService
from ..domain.exceptions import ResourceNotFoundException, ValidationException
from ..infrastructure.adapters import DjangoConfigurationRepository
from .serializers import ConfigurationSerializer, ConfigurationCreateSerializer, ConfigurationUpdateSerializer


class ConfigurationViewSet(viewsets.ViewSet):
    """
    ViewSet pour les configurations d'équipements.
    
    Ce ViewSet fournit des endpoints pour gérer les configurations d'équipements.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        """
        Initialise une nouvelle instance de ConfigurationViewSet.
        """
        super().__init__(**kwargs)
        # Pour l'instant, on utilise le repository directement au lieu du service complet
        # Dans une vraie implémentation, on aurait tous les adaptateurs nécessaires
        self._repository = DjangoConfigurationRepository()
    
    @swagger_auto_schema(
        operation_summary="Liste des configurations",
        operation_description="Récupère la liste des configurations d'équipements",
        responses={
            200: openapi.Response("Liste des configurations", ConfigurationSerializer(many=True)),
            500: "Erreur serveur"
        },
        tags=['Network Management']
    )
    def list(self, request: Request) -> Response:
        """
        Liste toutes les configurations d'équipements.
        
        Args:
            request (Request): La requête HTTP.
            
        Returns:
            Response: La réponse HTTP contenant la liste des configurations.
        """
        try:
            # Récupérer les paramètres de requête
            device_id = request.query_params.get('device_id')
            
            # Récupérer les configurations
            if device_id:
                configs = self._repository.get_by_device_id(int(device_id))
            else:
                # Pour éviter de récupérer toutes les configurations (potentiellement nombreuses),
                # on demande un filtre
                return Response(
                    {'error': 'Please provide a device_id parameter'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convertir en dictionnaires pour la sérialisation
            config_data = []
            for config in configs:
                config_data.append({
                    'id': config.id,
                    'device_id': config.device.id,
                    'content': config.content,
                    'version': config.version,
                    'is_active': config.is_active,
                    'status': config.status,
                    'comment': config.comment,
                    'created_by': config.created_by,
                    'created_at': config.created_at,
                    'applied_at': config.applied_at
                })
            
            # Sérialiser les configurations
            serializer = ConfigurationSerializer(config_data, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request: Request, pk=None) -> Response:
        """
        Récupère une configuration d'équipement par son ID.
        
        Args:
            request (Request): La requête HTTP.
            pk: L'ID de la configuration à récupérer.
            
        Returns:
            Response: La réponse HTTP contenant la configuration.
        """
        try:
            # Récupérer la configuration
            config = self._repository.get_by_id(int(pk))
            
            if not config:
                return Response({'error': 'Configuration not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Convertir en dictionnaire pour la sérialisation
            config_data = {
                'id': config.id,
                'device_id': config.device.id,
                'content': config.content,
                'version': config.version,
                'is_active': config.is_active,
                'status': config.status,
                'comment': config.comment,
                'created_by': config.created_by,
                'created_at': config.created_at,
                'applied_at': config.applied_at
            }
            
            # Sérialiser la configuration
            serializer = ConfigurationSerializer(config_data)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def create(self, request: Request) -> Response:
        """
        Crée une nouvelle configuration d'équipement.
        
        Args:
            request (Request): La requête HTTP contenant les données de la configuration.
            
        Returns:
            Response: La réponse HTTP contenant la configuration créée.
        """
        try:
            # Import des services nécessaires
            from ..application.services import ConfigurationService
            from ..infrastructure.adapters import DjangoConfigurationRepository
            from .serializers import ConfigurationCreateSerializer, ConfigurationSerializer
            
            # Validation des données
            serializer = ConfigurationCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer le service de configuration
            repository = DjangoConfigurationRepository()
            config_service = ConfigurationService(repository)
            
            # Créer la configuration
            config_data = serializer.validated_data
            config = config_service.create_configuration(config_data)
            
            # Retourner la réponse
            response_serializer = ConfigurationSerializer(config)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de configuration: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request: Request, pk=None) -> Response:
        """
        Met à jour une configuration d'équipement existante.
        
        Args:
            request (Request): La requête HTTP contenant les nouvelles données de la configuration.
            pk: L'ID de la configuration à mettre à jour.
            
        Returns:
            Response: La réponse HTTP contenant la configuration mise à jour.
        """
        try:
            # Import des services nécessaires
            from ..application.services import ConfigurationService
            from ..infrastructure.adapters import DjangoConfigurationRepository
            from .serializers import ConfigurationUpdateSerializer, ConfigurationSerializer
            
            # Validation des données
            serializer = ConfigurationUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Créer le service de configuration
            repository = DjangoConfigurationRepository()
            config_service = ConfigurationService(repository)
            
            # Mettre à jour la configuration
            config_data = serializer.validated_data
            config = config_service.update_configuration(int(pk), config_data)
            
            if not config:
                return Response(
                    {'error': f'Configuration avec ID {pk} non trouvée'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Retourner la réponse
            response_serializer = ConfigurationSerializer(config)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de configuration: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def partial_update(self, request: Request, pk=None) -> Response:
        """
        Met à jour partiellement une configuration d'équipement existante.
        
        Args:
            request (Request): La requête HTTP contenant les nouvelles données de la configuration.
            pk: L'ID de la configuration à mettre à jour.
            
        Returns:
            Response: La réponse HTTP contenant la configuration mise à jour.
        """
        return self.update(request, pk)
    
    def destroy(self, request: Request, pk=None) -> Response:
        """
        Supprime une configuration d'équipement.
        
        Args:
            request (Request): La requête HTTP.
            pk: L'ID de la configuration à supprimer.
            
        Returns:
            Response: La réponse HTTP indiquant le succès ou l'échec de la suppression.
        """
        try:
            # Supprimer la configuration
            success = self._repository.delete(int(pk))
            
            if success:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'Failed to delete configuration'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def activate(self, request: Request, pk=None) -> Response:
        """
        Active une configuration d'équipement.
        
        Args:
            request (Request): La requête HTTP.
            pk: L'ID de la configuration à activer.
            
        Returns:
            Response: La réponse HTTP contenant la configuration activée.
        """
        try:
            # Pour simplifier, on retourne un message d'information
            return Response({
                'message': 'Configuration activation not implemented in simplified version',
                'info': 'Use the full service implementation for complete functionality'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
