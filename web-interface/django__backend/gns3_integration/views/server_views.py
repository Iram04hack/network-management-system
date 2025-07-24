"""
Vues REST pour les serveurs GNS3.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.core.exceptions import ObjectDoesNotExist

from ..di_container import gns3_container
from ..serializers import ServerSerializer, ServerDetailSerializer
from ..domain.exceptions import GNS3ConnectionError


class ServerViewSet(viewsets.ViewSet):
    """
    API pour la gestion des serveurs GNS3.
    """
    
    @property
    def server_service(self):
        """Récupère le service de gestion des serveurs depuis le conteneur DI."""
        return gns3_container.server_service()

    @swagger_auto_schema(
        operation_summary="Liste tous les serveurs GNS3",
        operation_description="Retourne la liste de tous les serveurs GNS3 enregistrés",
        
        tags=['GNS3 Integration'],
        responses={
            200: openapi.Response(
                description="Liste des serveurs GNS3",
                schema=ServerSerializer
            ),
            500: "Erreur interne du serveur"
        }
    )
    def list(self, request):
        """
        Liste tous les serveurs GNS3 enregistrés.
        """
        try:
            servers = self.server_service.get_all_servers()
            serializer = ServerSerializer(servers, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Récupère un serveur GNS3 spécifique",
        operation_description="Retourne les détails d'un serveur GNS3 spécifique",
        
        tags=['GNS3 Integration'],responses={
            200: openapi.Response(
                description="Détails du serveur GNS3",
                schema=ServerDetailSerializer()
            ),
            404: "Serveur non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def retrieve(self, request, pk=None):
        """
        Récupère les détails d'un serveur GNS3 spécifique.
        """
        try:
            server = self.server_service.get_server(pk)
            serializer = ServerDetailSerializer(server)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Serveur avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Crée un nouveau serveur GNS3",
        operation_description="Crée un nouveau serveur GNS3 avec les informations fournies",
        
        tags=['GNS3 Integration'],request_body=ServerDetailSerializer,
        responses={
            201: openapi.Response(
                description="Serveur GNS3 créé avec succès",
                schema=ServerDetailSerializer()
            ),
            400: "Données invalides",
            500: "Erreur interne du serveur"
        }
    )
    def create(self, request):
        """
        Crée un nouveau serveur GNS3.
        """
        serializer = ServerDetailSerializer(data=request.data)
        if serializer.is_valid():
            try:
                server = self.server_service.create_server(serializer.validated_data)
                return Response(
                    ServerDetailSerializer(server).data,
                    status=status.HTTP_201_CREATED
                )
            except GNS3ConnectionError as e:
                return Response(
                    {"error": f"Impossible de se connecter au serveur GNS3: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Met à jour un serveur GNS3 existant",
        operation_description="Met à jour les informations d'un serveur GNS3 existant",
        
        tags=['GNS3 Integration'],request_body=ServerDetailSerializer,
        responses={
            200: openapi.Response(
                description="Serveur GNS3 mis à jour avec succès",
                schema=ServerDetailSerializer()
            ),
            400: "Données invalides",
            404: "Serveur non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def update(self, request, pk=None):
        """
        Met à jour un serveur GNS3 existant.
        """
        try:
            server = self.server_service.get_server(pk)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Serveur avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ServerDetailSerializer(data=request.data)
        if serializer.is_valid():
            try:
                updated_server = self.server_service.update_server(
                    pk, serializer.validated_data
                )
                return Response(ServerDetailSerializer(updated_server).data)
            except GNS3ConnectionError as e:
                return Response(
                    {"error": f"Impossible de se connecter au serveur GNS3: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Supprime un serveur GNS3",
        operation_description="Supprime un serveur GNS3 existant",
        
        tags=['GNS3 Integration'],responses={
            204: "Serveur supprimé avec succès",
            404: "Serveur non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def destroy(self, request, pk=None):
        """
        Supprime un serveur GNS3 existant.
        """
        try:
            self.server_service.delete_server(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Serveur avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @swagger_auto_schema(
        operation_summary="Teste la connexion à un serveur GNS3",
        operation_description="Vérifie si la connexion au serveur GNS3 est fonctionnelle",
        
        tags=['GNS3 Integration'],responses={
            200: "Connexion réussie",
            400: "Échec de la connexion",
            404: "Serveur non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['get'])
    def test_connection(self, request, pk=None):
        """
        Teste la connexion à un serveur GNS3 spécifique.
        """
        try:
            result = self.server_service.test_connection(pk)
            if result:
                return Response({"status": "success", "message": "Connexion réussie"})
            else:
                return Response(
                    {"status": "error", "message": "Échec de la connexion"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Serveur avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
 