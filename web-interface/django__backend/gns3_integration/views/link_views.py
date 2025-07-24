"""
Vues REST pour les liens GNS3.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.core.exceptions import ObjectDoesNotExist

from ..di_container import gns3_container
from ..serializers import LinkSerializer
from ..domain.exceptions import GNS3LinkError, GNS3ConnectionError


class LinkViewSet(viewsets.ViewSet):
    """
    API pour la gestion des liens GNS3.
    """
    
    @property
    def link_service(self):
        """Récupère le service de gestion des liens depuis le conteneur DI."""
        return gns3_container.link_service()

    @swagger_auto_schema(
        operation_summary="Liste tous les liens d'un projet GNS3",
        operation_description="Retourne la liste de tous les liens d'un projet GNS3 spécifique",
        
        tags=['GNS3 Integration'],manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet GNS3",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Liste des liens GNS3",
                schema=LinkSerializer
            ),
            400: "ID du projet non fourni",
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def list(self, request):
        """
        Liste tous les liens d'un projet GNS3 spécifique.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            links = self.link_service.get_all_links(project_id)
            serializer = LinkSerializer(links, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Projet avec l'ID {project_id} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Récupère un lien GNS3 spécifique",
        operation_description="Retourne les détails d'un lien GNS3 spécifique",
        
        tags=['GNS3 Integration'],manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet GNS3",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Détails du lien GNS3",
                schema=LinkSerializer()
            ),
            400: "ID du projet non fourni",
            404: "Lien ou projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def retrieve(self, request, pk=None):
        """
        Récupère les détails d'un lien GNS3 spécifique.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            link = self.link_service.get_link(project_id, pk)
            serializer = LinkSerializer(link)
            return Response(serializer.data)
        except ObjectDoesNotExist as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Crée un nouveau lien GNS3",
        operation_description="Crée un nouveau lien GNS3 dans un projet spécifique",
        
        tags=['GNS3 Integration'],request_body=LinkSerializer,
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet GNS3",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response(
                description="Lien GNS3 créé avec succès",
                schema=LinkSerializer()
            ),
            400: "Données invalides ou ID du projet non fourni",
            404: "Projet ou nœud non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def create(self, request):
        """
        Crée un nouveau lien GNS3 dans un projet spécifique.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = LinkSerializer(data=request.data)
        if serializer.is_valid():
            try:
                link = self.link_service.create_link(
                    project_id, serializer.validated_data
                )
                return Response(
                    LinkSerializer(link).data,
                    status=status.HTTP_201_CREATED
                )
            except ObjectDoesNotExist as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_404_NOT_FOUND
                )
            except GNS3ConnectionError as e:
                return Response(
                    {"error": f"Impossible de se connecter au serveur GNS3: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except GNS3LinkError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Supprime un lien GNS3",
        operation_description="Supprime un lien GNS3 existant",
        
        tags=['GNS3 Integration'],manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="ID du projet GNS3",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            204: "Lien supprimé avec succès",
            400: "ID du projet non fourni",
            404: "Lien ou projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def destroy(self, request, pk=None):
        """
        Supprime un lien GNS3 existant.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            self.link_service.delete_link(project_id, pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 