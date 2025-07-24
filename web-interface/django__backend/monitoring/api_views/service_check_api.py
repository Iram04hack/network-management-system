"""
Vues API pour la gestion des vérifications de service.
"""

from datetime import datetime
from typing import List, Dict, Any

from django.utils.dateparse import parse_datetime
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..di_container import resolve
from ..domain.interfaces.repositories import (
    ServiceCheckRepository,
    DeviceServiceCheckRepository,
    CheckResultRepository
)
from ..domain.services import AlertingService
from ..use_cases.service_check_use_cases import (
    ServiceCheckUseCase,
    DeviceServiceCheckUseCase,
    CheckResultUseCase
)
from ..serializers.service_check_serializers import (
    ServiceCheckSerializer,
    DeviceServiceCheckSerializer,
    CheckResultSerializer
)


class ServiceCheckViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des vérifications de service."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Utiliser le conteneur DI au lieu d'instanciation directe
        self.repository = resolve('service_check_repository')
        self.use_case = ServiceCheckUseCase(self.repository)
    
    @swagger_auto_schema(
        operation_summary="Liste des vérifications de service",
        operation_description="Récupère la liste des vérifications de service avec filtres optionnels.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, description="Filtrer par catégorie", type=openapi.TYPE_STRING),
            openapi.Parameter('check_type', openapi.IN_QUERY, description="Filtrer par type de vérification", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description='Liste des servicechecks',
                schema=ServiceCheckSerializer
            ),
            401: "Non authentifié"
        }
    )
    def list(self, request: Request) -> Response:
        """Liste toutes les vérifications de service."""
        # Extraire les filtres de la requête
        filters = {}
        if 'category' in request.query_params:
            filters['category'] = request.query_params['category']
        if 'check_type' in request.query_params:
            filters['check_type'] = request.query_params['check_type']
        
        # Récupérer les vérifications de service
        service_checks = self.use_case.list_service_checks(filters)
        
        # Sérialiser les résultats
        serializer = ServiceCheckSerializer(service_checks, many=True)
        
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Détails d'une vérification de service",
        operation_description="Récupère les détails d'une vérification de service par son ID.",
        tags=['Monitoring'],
        responses={
            200: openapi.Response(
                description='Détails du service check',
                schema=ServiceCheckSerializer()
            ),
            404: "Vérification de service non trouvée",
            401: "Non authentifié"
        }
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère une vérification de service par son ID."""
        try:
            service_check = self.use_case.get_service_check(int(pk))
            serializer = ServiceCheckSerializer(service_check)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Créer une vérification de service",
        operation_description="Crée une nouvelle vérification de service dans le système.",
        tags=['Monitoring'],
        request_body=ServiceCheckSerializer,
        responses={
            201: openapi.Response(
                description='Vérification de service créée',
                schema=ServiceCheckSerializer()
            ),
            400: "Données invalides",
            401: "Non authentifié"
        }
    )
    def create(self, request: Request) -> Response:
        """Crée une nouvelle vérification de service."""
        # Valider les données d'entrée
        serializer = ServiceCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer la vérification de service
        try:
            service_check = self.use_case.create_service_check(
                name=serializer.validated_data['name'],
                check_type=serializer.validated_data['check_type'],
                check_config=serializer.validated_data['check_config'],
                description=serializer.validated_data.get('description'),
                category=serializer.validated_data.get('category'),
                compatible_device_types=serializer.validated_data.get('compatible_device_types'),
                enabled=serializer.validated_data.get('enabled', True)
            )
            
            # Sérialiser la réponse
            response_serializer = ServiceCheckSerializer(service_check)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Modifier une vérification de service",
        operation_description="Met à jour complètement une vérification de service existante.",
        tags=['Monitoring'],
        request_body=ServiceCheckSerializer,
        responses={
            200: openapi.Response(
                description='Vérification de service mise à jour',
                schema=ServiceCheckSerializer()
            ),
            400: "Données invalides",
            404: "Vérification de service non trouvée",
            401: "Non authentifié"
        }
    )
    def update(self, request: Request, pk=None) -> Response:
        """Met à jour une vérification de service."""
        # Valider les données d'entrée
        serializer = ServiceCheckSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour la vérification de service
        try:
            # Si la configuration est mise à jour, utiliser la méthode spécifique
            if 'check_config' in serializer.validated_data:
                service_check = self.use_case.update_check_config(
                    service_check_id=int(pk),
                    new_config=serializer.validated_data['check_config']
                )
                # Supprimer check_config pour ne pas le mettre à jour deux fois
                validated_data = dict(serializer.validated_data)
                validated_data.pop('check_config')
                
                # Mettre à jour les autres champs si nécessaire
                if validated_data:
                    service_check = self.repository.update(int(pk), **validated_data)
            else:
                # Mise à jour standard
                service_check = self.repository.update(int(pk), **serializer.validated_data)
            
            # Sérialiser la réponse
            response_serializer = ServiceCheckSerializer(service_check)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Supprimer une vérification de service",
        operation_description="Supprime une vérification de service du système.",
        tags=['Monitoring'],
        responses={
            204: "Vérification de service supprimée avec succès",
            404: "Vérification de service non trouvée",
            401: "Non authentifié"
        }
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime une vérification de service."""
        try:
            result = self.repository.delete(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Failed to delete service check"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


class DeviceServiceCheckViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des vérifications de service d'équipement."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Utiliser le conteneur DI au lieu d'instanciation directe
        self.repository = resolve('device_service_check_repository')
        self.service_check_repository = resolve('service_check_repository')
        self.use_case = DeviceServiceCheckUseCase(
            self.repository,
            self.service_check_repository
        )
    
    @swagger_auto_schema(
        operation_summary="Liste des vérifications d'équipement",
        operation_description="Récupère la liste des vérifications de service configurées pour les équipements.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('device_id', openapi.IN_QUERY, description="Filtrer par ID d'équipement", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response('Liste des deviceservicechecks', schema=DeviceServiceCheckSerializer),
            401: "Non authentifié"
        }
    )
    def list(self, request: Request) -> Response:
        """Liste toutes les vérifications de service d'équipement."""
        # Extraire les filtres de la requête
        device_id = request.query_params.get('device_id')
        if device_id:
            device_checks = self.use_case.list_device_checks(device_id=int(device_id))
        else:
            device_checks = self.use_case.list_device_checks()
        
        # Sérialiser les résultats
        serializer = DeviceServiceCheckSerializer(device_checks, many=True)
        
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Détails d'une vérification d'équipement",
        operation_description="Récupère les détails d'une vérification de service d'équipement par son ID.",
        tags=['Monitoring'],
        responses={200: DeviceServiceCheckSerializer, 404: "Vérification non trouvée", 401: "Non authentifié"}
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère une vérification de service d'équipement par son ID."""
        try:
            device_check = self.use_case.get_device_check(int(pk))
            serializer = DeviceServiceCheckSerializer(device_check)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Créer une vérification d'équipement",
        operation_description="Crée une nouvelle vérification de service pour un équipement spécifique.",
        tags=['Monitoring'],
        request_body=DeviceServiceCheckSerializer,
        responses={201: DeviceServiceCheckSerializer, 400: "Données invalides", 401: "Non authentifié"}
    )
    def create(self, request: Request) -> Response:
        """Crée une nouvelle vérification de service d'équipement."""
        # Valider les données d'entrée
        serializer = DeviceServiceCheckSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer la vérification de service d'équipement
        try:
            device_check = self.use_case.create_device_check(
                device_id=serializer.validated_data['device_id'],
                service_check_id=serializer.validated_data['service_check_id'],
                name=serializer.validated_data.get('name'),
                specific_config=serializer.validated_data.get('specific_config'),
                check_interval=serializer.validated_data.get('check_interval', 300),
                is_active=serializer.validated_data.get('is_active', True)
            )
            
            # Sérialiser la réponse
            response_serializer = DeviceServiceCheckSerializer(device_check)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Modifier une vérification d'équipement",
        operation_description="Met à jour les paramètres d'une vérification de service d'équipement.",
        tags=['Monitoring'],
        request_body=DeviceServiceCheckSerializer,
        responses={200: DeviceServiceCheckSerializer, 400: "Données invalides", 404: "Vérification non trouvée", 401: "Non authentifié"}
    )
    def update(self, request: Request, pk=None) -> Response:
        """Met à jour une vérification de service d'équipement."""
        # Valider les données d'entrée
        serializer = DeviceServiceCheckSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Mettre à jour la vérification de service d'équipement
        try:
            device_check = self.repository.update(int(pk), **serializer.validated_data)
            
            # Sérialiser la réponse
            response_serializer = DeviceServiceCheckSerializer(device_check)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Supprimer une vérification d'équipement",
        operation_description="Supprime définitivement une vérification de service d'équipement.",
        tags=['Monitoring'],
        responses={204: "Suppression réussie", 404: "Vérification non trouvée", 401: "Non authentifié"}
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """Supprime une vérification de service d'équipement."""
        try:
            result = self.repository.delete(int(pk))
            if result:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Failed to delete device service check"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Exécuter une vérification d'équipement",
        operation_description="Lance l'exécution manuelle d'une vérification de service pour un équipement spécifique.",
        tags=['Monitoring'],
        responses={200: "Vérification lancée", 404: "Vérification non trouvée", 401: "Non authentifié"}
    )
    @action(detail=True, methods=['post'])
    def run_check(self, request: Request, pk=None) -> Response:
        """Exécute une vérification de service d'équipement."""
        try:
            # Vérifier que la vérification existe
            device_check = self.use_case.get_device_check(int(pk))
            
            # Lancer la tâche d'exécution de la vérification
            from ..tasks.service_check_tasks import run_service_check
            task = run_service_check.delay(int(pk))
            
            return Response({
                "message": "Service check execution started",
                "task_id": task.id
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CheckResultViewSet(viewsets.ViewSet):
    """Vue API pour la gestion des résultats de vérification."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Utiliser le conteneur DI au lieu d'instanciation directe
        self.repository = resolve('check_result_repository')
        self.device_service_check_repository = resolve('device_service_check_repository')
        self.alert_service = resolve('alerting_service')
        self.use_case = CheckResultUseCase(
            self.repository,
            self.device_service_check_repository,
            self.alert_service
        )
    
    @swagger_auto_schema(
        operation_summary="Liste des résultats de vérification",
        operation_description="Récupère la liste des résultats de vérification pour un équipement avec filtres optionnels.",
        tags=['Monitoring'],
        manual_parameters=[
            openapi.Parameter('device_check_id', openapi.IN_QUERY, description="ID de la vérification d'équipement (requis)", type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('start_time', openapi.IN_QUERY, description="Date de début (ISO format)", type=openapi.TYPE_STRING),
            openapi.Parameter('end_time', openapi.IN_QUERY, description="Date de fin (ISO format)", type=openapi.TYPE_STRING),
            openapi.Parameter('limit', openapi.IN_QUERY, description="Nombre maximum de résultats", type=openapi.TYPE_INTEGER),
        ],
        responses={200: CheckResultSerializer(many=True), 400: "Paramètre device_check_id manquant", 401: "Non authentifié"}
    )
    def list(self, request: Request) -> Response:
        """Liste les résultats de vérification pour une vérification de service d'équipement."""
        # Vérifier que l'ID de la vérification de service d'équipement est fourni
        device_check_id = request.query_params.get('device_check_id')
        if not device_check_id:
            return Response({"error": "device_check_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Extraire les paramètres de la requête
        start_time = None
        if 'start_time' in request.query_params:
            start_time = parse_datetime(request.query_params['start_time'])
        
        end_time = None
        if 'end_time' in request.query_params:
            end_time = parse_datetime(request.query_params['end_time'])
        
        limit = None
        if 'limit' in request.query_params:
            limit = int(request.query_params['limit'])
        
        # Récupérer les résultats de vérification
        try:
            check_results = self.use_case.get_check_results(
                device_check_id=int(device_check_id),
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            
            # Sérialiser les résultats
            serializer = CheckResultSerializer(check_results, many=True)
            
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Dernier résultat de vérification",
        operation_description="Récupère le dernier résultat d'une vérification de service d'équipement par son ID.",
        tags=['Monitoring'],
        responses={200: CheckResultSerializer, 404: "Résultat non trouvé", 401: "Non authentifié"}
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Récupère le dernier résultat d'une vérification de service d'équipement."""
        try:
            latest_result = self.use_case.get_latest_result(int(pk))
            if latest_result is None:
                return Response({"message": "No results found for this check"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = CheckResultSerializer(latest_result)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Créer un résultat de vérification",
        operation_description="Enregistre un nouveau résultat de vérification pour une vérification d'équipement.",
        tags=['Monitoring'],
        request_body=CheckResultSerializer,
        responses={201: CheckResultSerializer, 400: "Données invalides", 401: "Non authentifié"}
    )
    def create(self, request: Request) -> Response:
        """Crée un nouveau résultat de vérification."""
        # Valider les données d'entrée
        serializer = CheckResultSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer le résultat de vérification
        try:
            check_result = self.use_case.create_check_result(
                device_check_id=serializer.validated_data['device_service_check_id'],
                status=serializer.validated_data['status'],
                execution_time=serializer.validated_data['execution_time'],
                message=serializer.validated_data.get('message'),
                details=serializer.validated_data.get('details')
            )
            
            # Sérialiser la réponse
            response_serializer = CheckResultSerializer(check_result)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST) 