"""
Vues REST pour les templates GNS3.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.core.exceptions import ObjectDoesNotExist

from ..di_container import gns3_container
from ..serializers import TemplateSerializer
from ..domain.exceptions import GNS3ConnectionError


class TemplateViewSet(viewsets.ViewSet):
    """
    API pour la gestion des templates GNS3.
    """
    
    @property
    def template_service(self):
        """Récupère le service de gestion des templates depuis le conteneur DI."""
        return gns3_container.template_service()

    @swagger_auto_schema(
        operation_summary="Liste tous les templates GNS3",
        operation_description="Retourne la liste de tous les templates GNS3 disponibles sur un serveur",
        
        tags=['GNS3 Integration'],manual_parameters=[
            openapi.Parameter(
                'server_id',
                openapi.IN_QUERY,
                description="ID du serveur GNS3",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Liste des templates GNS3",
                schema=TemplateSerializer
            ),
            400: "ID du serveur non fourni",
            404: "Serveur non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def list(self, request):
        """
        Liste tous les templates GNS3 disponibles sur un serveur.
        """
        server_id = request.query_params.get('server_id')
        if not server_id:
            return Response(
                {"error": "Le paramètre 'server_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            templates = self.template_service.get_all_templates(server_id)
            serializer = TemplateSerializer(templates, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Serveur avec l'ID {server_id} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Récupère un template GNS3 spécifique",
        operation_description="Retourne les détails d'un template GNS3 spécifique",
        
        tags=['GNS3 Integration'],manual_parameters=[
            openapi.Parameter(
                'server_id',
                openapi.IN_QUERY,
                description="ID du serveur GNS3",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Détails du template GNS3",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'id': openapi.Schema(type=openapi.TYPE_INTEGER), 'name': openapi.Schema(type=openapi.TYPE_STRING)})
            ),
            400: "ID du serveur non fourni",
            404: "Template ou serveur non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def retrieve(self, request, pk=None):
        """
        Récupère les détails d'un template GNS3 spécifique.
        """
        server_id = request.query_params.get('server_id')
        if not server_id:
            return Response(
                {"error": "Le paramètre 'server_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            template = self.template_service.get_template(server_id, pk)
            serializer = TemplateSerializer(template)
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
        operation_summary="Crée un nouveau template GNS3",
        operation_description="Crée un nouveau template GNS3 sur un serveur spécifique",
        
        tags=['GNS3 Integration'],request_body=TemplateSerializer,
        manual_parameters=[
            openapi.Parameter(
                'server_id',
                openapi.IN_QUERY,
                description="ID du serveur GNS3",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            201: openapi.Response(
                description="Template GNS3 créé avec succès",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'id': openapi.Schema(type=openapi.TYPE_INTEGER), 'name': openapi.Schema(type=openapi.TYPE_STRING)})
            ),
            400: "Données invalides ou ID du serveur non fourni",
            404: "Serveur non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def create(self, request):
        """
        Crée un nouveau template GNS3 sur un serveur spécifique.
        """
        server_id = request.query_params.get('server_id')
        if not server_id:
            return Response(
                {"error": "Le paramètre 'server_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = TemplateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                template = self.template_service.create_template(
                    server_id, serializer.validated_data
                )
                return Response(
                    TemplateSerializer(template).data,
                    status=status.HTTP_201_CREATED
                )
            except ObjectDoesNotExist:
                return Response(
                    {"error": f"Serveur avec l'ID {server_id} non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
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
        operation_summary="Met à jour un template GNS3 existant",
        operation_description="Met à jour les informations d'un template GNS3 existant",
        
        tags=['GNS3 Integration'],request_body=TemplateSerializer,
        manual_parameters=[
            openapi.Parameter(
                'server_id',
                openapi.IN_QUERY,
                description="ID du serveur GNS3",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Template GNS3 mis à jour avec succès",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'id': openapi.Schema(type=openapi.TYPE_INTEGER), 'name': openapi.Schema(type=openapi.TYPE_STRING)})
            ),
            400: "Données invalides ou ID du serveur non fourni",
            404: "Template ou serveur non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def update(self, request, pk=None):
        """
        Met à jour un template GNS3 existant.
        """
        server_id = request.query_params.get('server_id')
        if not server_id:
            return Response(
                {"error": "Le paramètre 'server_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Vérifier si le template existe
            self.template_service.get_template(server_id, pk)
        except ObjectDoesNotExist as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TemplateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                updated_template = self.template_service.update_template(
                    server_id, pk, serializer.validated_data
                )
                return Response(TemplateSerializer(updated_template).data)
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
        operation_summary="Supprime un template GNS3",
        operation_description="Supprime un template GNS3 existant",
        
        tags=['GNS3 Integration'],manual_parameters=[
            openapi.Parameter(
                'server_id',
                openapi.IN_QUERY,
                description="ID du serveur GNS3",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            204: "Template supprimé avec succès",
            400: "ID du serveur non fourni",
            404: "Template ou serveur non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def destroy(self, request, pk=None):
        """
        Supprime un template GNS3 existant.
        """
        server_id = request.query_params.get('server_id')
        if not server_id:
            return Response(
                {"error": "Le paramètre 'server_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            self.template_service.delete_template(server_id, pk)
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