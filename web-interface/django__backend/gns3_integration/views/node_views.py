"""
Vues REST pour les nœuds GNS3.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.core.exceptions import ObjectDoesNotExist

from ..di_container import gns3_container
from ..serializers import NodeSerializer
from ..domain.exceptions import GNS3NodeError, GNS3ConnectionError


class NodeViewSet(viewsets.ViewSet):
    """
    API pour la gestion des nœuds GNS3.
    """
    
    @property
    def node_service(self):
        """Récupère le service de gestion des nœuds depuis le conteneur DI."""
        return gns3_container.node_service()

    @swagger_auto_schema(
        operation_summary="Liste tous les nœuds d'un projet GNS3",
        operation_description="Retourne la liste de tous les nœuds d'un projet GNS3 spécifique",
        
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
                description="Liste des nœuds GNS3",
                schema=NodeSerializer
            ),
            400: "ID du projet non fourni",
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def list(self, request):
        """
        Liste tous les nœuds d'un projet GNS3 spécifique.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            nodes = self.node_service.list_nodes(project_id)
            serializer = NodeSerializer(nodes, many=True)
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
        operation_summary="Récupère un nœud GNS3 spécifique",
        operation_description="Retourne les détails d'un nœud GNS3 spécifique",
        
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
                description="Détails du nœud GNS3",
                schema=NodeSerializer()
            ),
            400: "ID du projet non fourni",
            404: "Nœud ou projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def retrieve(self, request, pk=None):
        """
        Récupère les détails d'un nœud GNS3 spécifique.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            node = self.node_service.get_node(project_id, pk)
            serializer = NodeSerializer(node)
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
        operation_summary="Crée un nouveau nœud GNS3",
        operation_description="Crée un nouveau nœud GNS3 dans un projet spécifique",
        
        tags=['GNS3 Integration'],request_body=NodeSerializer,
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
                description="Nœud GNS3 créé avec succès",
                schema=NodeSerializer()
            ),
            400: "Données invalides ou ID du projet non fourni",
            404: "Projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def create(self, request):
        """
        Crée un nouveau nœud GNS3 dans un projet spécifique.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = NodeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                node = self.node_service.create_node(
                    project_id, serializer.validated_data
                )
                return Response(
                    NodeSerializer(node).data,
                    status=status.HTTP_201_CREATED
                )
            except ObjectDoesNotExist:
                return Response(
                    {"error": f"Projet avec l'ID {project_id} non trouvé"},
                    status=status.HTTP_404_NOT_FOUND
                )
            except GNS3ConnectionError as e:
                return Response(
                    {"error": f"Impossible de se connecter au serveur GNS3: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except GNS3NodeError as e:
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
        operation_summary="Met à jour un nœud GNS3 existant",
        operation_description="Met à jour les informations d'un nœud GNS3 existant",
        
        tags=['GNS3 Integration'],request_body=NodeSerializer,
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
            200: openapi.Response(
                description="Nœud GNS3 mis à jour avec succès",
                schema=NodeSerializer()
            ),
            400: "Données invalides ou ID du projet non fourni",
            404: "Nœud ou projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def update(self, request, pk=None):
        """
        Met à jour un nœud GNS3 existant.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Vérifier si le nœud existe
            self.node_service.get_node(project_id, pk)
        except ObjectDoesNotExist as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = NodeSerializer(data=request.data)
        if serializer.is_valid():
            try:
                updated_node = self.node_service.update_node(
                    project_id, pk, serializer.validated_data
                )
                return Response(NodeSerializer(updated_node).data)
            except GNS3ConnectionError as e:
                return Response(
                    {"error": f"Impossible de se connecter au serveur GNS3: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except GNS3NodeError as e:
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
        operation_summary="Supprime un nœud GNS3",
        operation_description="Supprime un nœud GNS3 existant",
        
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
            204: "Nœud supprimé avec succès",
            400: "ID du projet non fourni",
            404: "Nœud ou projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def destroy(self, request, pk=None):
        """
        Supprime un nœud GNS3 existant.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            self.node_service.delete_node(project_id, pk)
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
            
    @swagger_auto_schema(
        operation_summary="Démarre un nœud GNS3",
        operation_description="Démarre un nœud GNS3 spécifique",
        
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
            200: "Nœud démarré avec succès",
            400: "ID du projet non fourni",
            404: "Nœud ou projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Démarre un nœud GNS3 spécifique.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            node = self.node_service.start_node(project_id, pk)
            return Response({
                "status": "success", 
                "message": f"Nœud {node.name} démarré avec succès"
            })
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
        operation_summary="Arrête un nœud GNS3",
        operation_description="Arrête un nœud GNS3 spécifique",
        
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
            200: "Nœud arrêté avec succès",
            400: "ID du projet non fourni",
            404: "Nœud ou projet non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """
        Arrête un nœud GNS3 spécifique.
        """
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"error": "Le paramètre 'project_id' est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            node = self.node_service.stop_node(project_id, pk)
            return Response({
                "status": "success", 
                "message": f"Nœud {node.name} arrêté avec succès"
            })
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
