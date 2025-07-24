"""
Vues REST pour les scripts GNS3.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.core.exceptions import ObjectDoesNotExist

from ..di_container import gns3_container
from ..serializers import ScriptSerializer, ScriptExecutionSerializer
from ..domain.exceptions import GNS3Exception, GNS3ConnectionError


class ScriptViewSet(viewsets.ViewSet):
    """
    API pour la gestion des scripts GNS3.
    """
    
    @property
    def script_service(self):
        """Récupère le service de gestion des scripts depuis le conteneur DI."""
        try:
            return gns3_container.script_service()
        except Exception:
            # Fallback en cas d'échec du conteneur DI
            from ..application.script_service import ScriptService
            from ..infrastructure.gns3_client_impl import GNS3ClientImpl
            from ..infrastructure.gns3_repository_impl import GNS3RepositoryImpl
            return ScriptService(GNS3ClientImpl(), GNS3RepositoryImpl())

    @swagger_auto_schema(
        operation_summary="Liste tous les scripts GNS3",
        operation_description="Retourne la liste de tous les scripts GNS3 disponibles",
        
        tags=['GNS3 Integration'],responses={
            200: openapi.Response(
                description="Liste des scripts GNS3",
                schema=ScriptSerializer
            ),
            500: "Erreur interne du serveur"
        }
    )
    def list(self, request):
        """
        Liste tous les scripts GNS3 disponibles.
        """
        try:
            scripts = self.script_service.list_scripts()
            serializer = ScriptSerializer(scripts, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Récupère un script GNS3 spécifique",
        operation_description="Retourne les détails d'un script GNS3 spécifique",
        
        tags=['GNS3 Integration'],responses={
            200: openapi.Response(
                description="Détails du script GNS3",
                schema=ScriptSerializer()
            ),
            404: "Script non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def retrieve(self, request, pk=None):
        """
        Récupère les détails d'un script GNS3 spécifique.
        """
        try:
            script = self.script_service.get_script(pk)
            serializer = ScriptSerializer(script)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Script avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Crée un nouveau script GNS3",
        operation_description="Crée un nouveau script GNS3 avec le contenu fourni",
        
        tags=['GNS3 Integration'],request_body=ScriptSerializer,
        responses={
            201: openapi.Response(
                description="Script GNS3 créé avec succès",
                schema=ScriptSerializer()
            ),
            400: "Données invalides",
            500: "Erreur interne du serveur"
        }
    )
    def create(self, request):
        """
        Crée un nouveau script GNS3.
        """
        serializer = ScriptSerializer(data=request.data)
        if serializer.is_valid():
            try:
                script = self.script_service.create_script(
                    serializer.validated_data.get('name'),
                    serializer.validated_data.get('script_type'),
                    serializer.validated_data.get('content'),
                    serializer.validated_data.get('description', ''),
                    request.user if request.user.is_authenticated else None
                )
                return Response(
                    ScriptSerializer(script).data,
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Met à jour un script GNS3 existant",
        operation_description="Met à jour le contenu d'un script GNS3 existant",
        
        tags=['GNS3 Integration'],request_body=ScriptSerializer,
        responses={
            200: openapi.Response(
                description="Script GNS3 mis à jour avec succès",
                schema=ScriptSerializer()
            ),
            400: "Données invalides",
            404: "Script non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def update(self, request, pk=None):
        """
        Met à jour un script GNS3 existant.
        """
        try:
            script = self.script_service.get_script(pk)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Script avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ScriptSerializer(data=request.data)
        if serializer.is_valid():
            try:
                updated_script = self.script_service.update_script(
                    pk, **serializer.validated_data
                )
                return Response(ScriptSerializer(updated_script).data)
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Supprime un script GNS3",
        operation_description="Supprime un script GNS3 existant",
        
        tags=['GNS3 Integration'],responses={
            204: "Script supprimé avec succès",
            404: "Script non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    def destroy(self, request, pk=None):
        """
        Supprime un script GNS3 existant.
        """
        try:
            self.script_service.delete_script(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Script avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Exécute un script sur un nœud GNS3",
        operation_description="Lance l'exécution d'un script sur un nœud GNS3 spécifique",
        
        tags=['GNS3 Integration'],request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'project_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID du projet GNS3'),
                'node_id': openapi.Schema(type=openapi.TYPE_STRING, description='ID du nœud GNS3'),
                'parameters': openapi.Schema(type=openapi.TYPE_OBJECT, description='Paramètres du script')
            },
            required=['project_id', 'node_id']
        ),
        responses={
            202: openapi.Response(
                description="Exécution du script lancée",
                schema=ScriptExecutionSerializer()
            ),
            400: "Données invalides",
            404: "Script, projet ou nœud non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Exécute un script sur un nœud GNS3 spécifique.
        """
        try:
            project_id = request.data.get('project_id')
            node_id = request.data.get('node_id')
            parameters = request.data.get('parameters', {})
            
            if not project_id or not node_id:
                return Response(
                    {"error": "Les paramètres 'project_id' et 'node_id' sont requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            execution = self.script_service.execute_script(
                pk, project_id, node_id, parameters
            )
            return Response(
                ScriptExecutionSerializer(execution).data,
                status=status.HTTP_202_ACCEPTED
            )
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
        operation_summary="Récupère les exécutions d'un script",
        operation_description="Retourne l'historique des exécutions d'un script spécifique",
        
        tags=['GNS3 Integration'],responses={
            200: openapi.Response(
                description="Liste des exécutions du script",
                schema=ScriptExecutionSerializer
            ),
            404: "Script non trouvé",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """
        Récupère l'historique des exécutions d'un script.
        """
        try:
            executions = self.script_service.get_script_executions(pk)
            serializer = ScriptExecutionSerializer(executions, many=True)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Script avec l'ID {pk} non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Valide la syntaxe d'un script",
        operation_description="Vérifie si le script a une syntaxe valide",
        
        tags=['GNS3 Integration'],request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING, description='Contenu du script à valider'),
                'script_type': openapi.Schema(type=openapi.TYPE_STRING, description='Type du script')
            },
            required=['content', 'script_type']
        ),
        responses={
            200: "Script valide",
            400: "Script invalide ou données manquantes",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """
        Valide la syntaxe d'un script.
        """
        try:
            content = request.data.get('content')
            script_type = request.data.get('script_type')
            
            if not content or not script_type:
                return Response(
                    {"error": "Les paramètres 'content' et 'script_type' sont requis"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            is_valid, errors = self.script_service.validate_script(content, script_type)
            
            if is_valid:
                return Response({
                    "valid": True,
                    "message": "Le script est valide"
                })
            else:
                return Response({
                    "valid": False,
                    "errors": errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ScriptExecutionViewSet(viewsets.ViewSet):
    """
    API pour la gestion des exécutions de scripts GNS3.
    """
    
    @property
    def script_service(self):
        """Récupère le service de gestion des scripts depuis le conteneur DI."""
        return gns3_container.script_service()

    @swagger_auto_schema(
        operation_summary="Liste toutes les exécutions de scripts",
        operation_description="Retourne l'historique de toutes les exécutions de scripts",
        
        tags=['GNS3 Integration'],responses={
            200: openapi.Response(
                description="Liste des exécutions de scripts",
                schema=ScriptExecutionSerializer
            ),
            500: "Erreur interne du serveur"
        }
    )
    def list(self, request):
        """
        Liste toutes les exécutions de scripts.
        """
        try:
            executions = self.script_service.get_all_executions()
            serializer = ScriptExecutionSerializer(executions, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Récupère une exécution de script spécifique",
        operation_description="Retourne les détails d'une exécution de script",
        
        tags=['GNS3 Integration'],responses={
            200: openapi.Response(
                description="Détails de l'exécution de script",
                schema=ScriptExecutionSerializer()
            ),
            404: "Exécution non trouvée",
            500: "Erreur interne du serveur"
        }
    )
    def retrieve(self, request, pk=None):
        """
        Récupère les détails d'une exécution de script.
        """
        try:
            execution = self.script_service.get_execution(pk)
            serializer = ScriptExecutionSerializer(execution)
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Exécution avec l'ID {pk} non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Annule une exécution de script",
        operation_description="Annule une exécution de script en cours",
        
        tags=['GNS3 Integration'],responses={
            200: "Exécution annulée avec succès",
            404: "Exécution non trouvée",
            400: "Impossible d'annuler cette exécution",
            500: "Erreur interne du serveur"
        }
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Annule une exécution de script en cours.
        """
        try:
            result = self.script_service.cancel_execution(pk)
            if result:
                return Response({
                    "status": "success",
                    "message": "Exécution annulée avec succès"
                })
            else:
                return Response(
                    {"error": "Impossible d'annuler cette exécution"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ObjectDoesNotExist:
            return Response(
                {"error": f"Exécution avec l'ID {pk} non trouvée"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 