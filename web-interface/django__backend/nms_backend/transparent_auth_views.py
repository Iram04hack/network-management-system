"""
Vues d'authentification transparente pour le Network Management System.

Ce module fournit les endpoints API pour l'authentification transparente
permettant au frontend React de se connecter automatiquement aux APIs Django.
"""

import logging
import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    operation_summary="Authentification transparente",
    operation_description="""
    Authentifie un utilisateur de manière transparente en créant automatiquement
    un super_utilisateur Django si nécessaire. Permet l'accès complet aux APIs.
    
    **Fonctionnalités :**
    - Création automatique de super_utilisateur Django
    - Authentification transparente sans configuration manuelle
    - Accès complet à toutes les APIs backend
    - Gestion sécurisée des mots de passe
    """,
    tags=['Authentification'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='Nom d\'utilisateur'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Mot de passe'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email (optionnel)')
        },
        required=['username', 'password']
    ),
    responses={
        200: openapi.Response(
            description='Authentification réussie',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Succès'),
                'user': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID utilisateur'),
                    'username': openapi.Schema(type=openapi.TYPE_STRING, description='Nom d\'utilisateur'),
                    'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
                    'is_superuser': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Super utilisateur'),
                    'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Staff'),
                }),
                'transparent_auth': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Authentification transparente'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, description='Message de succès')
            })
        ),
        400: "Données invalides",
        401: "Identifiants invalides",
        500: "Erreur serveur"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def transparent_login(request):
    """
    Endpoint pour l'authentification transparente.
    """
    try:
        # Extraire les données de connexion
        data = request.data
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', f"{username}@nms.local")
        
        if not username or not password:
            return Response({
                'error': 'Nom d\'utilisateur et mot de passe requis',
                'transparent_auth': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer ou récupérer l'utilisateur Django
        user = get_or_create_superuser(username, email, password)
        
        if user:
            # Authentifier l'utilisateur
            authenticated_user = authenticate(
                request, 
                username=username, 
                password=password
            )
            
            if authenticated_user:
                login(request, authenticated_user)
                logger.info(f"✅ Utilisateur {username} connecté avec succès (transparent)")
                
                return Response({
                    'success': True,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_superuser': user.is_superuser,
                        'is_staff': user.is_staff,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                    },
                    'transparent_auth': True,
                    'message': 'Connexion réussie avec accès complet aux APIs',
                    'api_access': {
                        'all_modules': True,
                        'superuser_privileges': True,
                        'api_documentation': '/swagger/',
                        'endpoints_count': '200+',
                        'features': [
                            'AI Assistant',
                            'Monitoring temps réel',
                            'GNS3 Integration',
                            'Security Management',
                            'Reporting avancé',
                            'QoS Management'
                        ]
                    }
                })
            else:
                logger.warning(f"❌ Échec d'authentification pour {username}")
                return Response({
                    'error': 'Identifiants invalides',
                    'transparent_auth': False
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({
                'error': 'Impossible de créer ou récupérer l\'utilisateur',
                'transparent_auth': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'authentification transparente : {e}")
        return Response({
            'error': 'Erreur interne du serveur',
            'transparent_auth': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary="Déconnexion",
    operation_description="Déconnecte l'utilisateur de la session Django",
    tags=['Authentification'],
    responses={
        200: openapi.Response(
            description='Déconnexion réussie',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Succès'),
                'message': openapi.Schema(type=openapi.TYPE_STRING, description='Message de succès')
            })
        )
    }
)
@api_view(['POST'])
def transparent_logout(request):
    """
    Endpoint pour la déconnexion.
    """
    try:
        if request.user.is_authenticated:
            username = request.user.username
            logout(request)
            logger.info(f"👋 Utilisateur {username} déconnecté")
            
            return Response({
                'success': True,
                'message': 'Déconnexion réussie'
            })
        else:
            return Response({
                'success': True,
                'message': 'Aucune session active'
            })
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la déconnexion : {e}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary="Informations utilisateur",
    operation_description="Récupère les informations de l'utilisateur connecté",
    tags=['Authentification'],
    responses={
        200: openapi.Response(
            description='Informations utilisateur',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'authenticated': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Authentifié'),
                'user': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID utilisateur'),
                    'username': openapi.Schema(type=openapi.TYPE_STRING, description='Nom d\'utilisateur'),
                    'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
                    'is_superuser': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Super utilisateur'),
                    'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Staff'),
                })
            })
        ),
        401: "Non authentifié"
    }
)
@api_view(['GET'])
def user_info(request):
    """
    Endpoint pour récupérer les informations de l'utilisateur connecté.
    """
    try:
        if request.user.is_authenticated:
            return Response({
                'authenticated': True,
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'is_superuser': request.user.is_superuser,
                    'is_staff': request.user.is_staff,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name,
                    'last_login': request.user.last_login,
                    'date_joined': request.user.date_joined,
                },
                'session_info': {
                    'session_key': request.session.session_key,
                    'session_age': request.session.get_expiry_age(),
                },
                'api_access': {
                    'all_modules': True,
                    'superuser_privileges': request.user.is_superuser,
                    'api_documentation': '/swagger/',
                    'total_endpoints': '200+',
                    'available_modules': [
                        'AI Assistant',
                        'Monitoring',
                        'GNS3 Integration',
                        'Security Management',
                        'Reporting',
                        'QoS Management',
                        'Network Management',
                        'Dashboard',
                        'API Clients',
                        'API Views',
                        'Common Infrastructure'
                    ]
                }
            })
        else:
            return Response({
                'authenticated': False,
                'message': 'Non authentifié'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des informations utilisateur : {e}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary="Inscription transparente",
    operation_description="""
    Crée un nouveau compte utilisateur avec privilèges super_utilisateur Django.
    
    **Fonctionnalités :**
    - Création automatique de super_utilisateur Django
    - Validation des données d'inscription
    - Authentification automatique après inscription
    - Accès complet à toutes les APIs backend
    """,
    tags=['Authentification'],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='Nom d\'utilisateur'),
            'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Mot de passe'),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='Prénom (optionnel)'),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Nom (optionnel)')
        },
        required=['username', 'email', 'password']
    ),
    responses={
        201: openapi.Response(
            description='Inscription réussie',
            schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Succès'),
                'user': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID utilisateur'),
                    'username': openapi.Schema(type=openapi.TYPE_STRING, description='Nom d\'utilisateur'),
                    'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
                    'is_superuser': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Super utilisateur'),
                }),
                'message': openapi.Schema(type=openapi.TYPE_STRING, description='Message de succès')
            })
        ),
        400: "Données invalides",
        409: "Utilisateur déjà existant",
        500: "Erreur serveur"
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def transparent_register(request):
    """
    Endpoint pour l'inscription transparente.
    """
    try:
        # Extraire les données d'inscription
        data = request.data
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        if not username or not email or not password:
            return Response({
                'error': 'Nom d\'utilisateur, email et mot de passe requis',
                'transparent_auth': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier si l'utilisateur existe déjà
        if User.objects.filter(username=username).exists():
            return Response({
                'error': 'Un utilisateur avec ce nom d\'utilisateur existe déjà',
                'transparent_auth': False
            }, status=status.HTTP_409_CONFLICT)
        
        if User.objects.filter(email=email).exists():
            return Response({
                'error': 'Un utilisateur avec cet email existe déjà',
                'transparent_auth': False
            }, status=status.HTTP_409_CONFLICT)
        
        # Créer le nouvel utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_superuser=True,
            is_staff=True,
            is_active=True
        )
        
        logger.info(f"🆕 Nouveau super_utilisateur créé : {username}")
        
        # Authentifier automatiquement l'utilisateur
        authenticated_user = authenticate(
            request, 
            username=username, 
            password=password
        )
        
        if authenticated_user:
            login(request, authenticated_user)
            
            return Response({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_superuser': user.is_superuser,
                    'is_staff': user.is_staff,
                },
                'transparent_auth': True,
                'message': 'Inscription réussie avec accès complet aux APIs',
                'api_access': {
                    'all_modules': True,
                    'superuser_privileges': True,
                    'api_documentation': '/swagger/',
                    'endpoints_count': '200+',
                    'auto_authenticated': True
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Utilisateur créé mais échec d\'authentification',
                'transparent_auth': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except ValidationError as e:
        logger.error(f"❌ Erreur de validation lors de l'inscription : {e}")
        return Response({
            'error': 'Données invalides',
            'details': str(e),
            'transparent_auth': False
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'inscription transparente : {e}")
        return Response({
            'error': 'Erreur interne du serveur',
            'transparent_auth': False
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_or_create_superuser(username, email, password):
    """
    Crée ou récupère un super_utilisateur Django.
    """
    try:
        # Vérifier si l'utilisateur existe déjà
        try:
            user = User.objects.get(username=username)
            logger.info(f"👤 Utilisateur {username} trouvé (existant)")
            
            # Mettre à jour le mot de passe si nécessaire
            if not user.check_password(password):
                user.set_password(password)
                user.save()
                logger.info(f"🔒 Mot de passe mis à jour pour {username}")
            
            # S'assurer que l'utilisateur est super_utilisateur
            if not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                user.save()
                logger.info(f"⚡ Privilèges super_utilisateur accordés à {username}")
            
            return user
            
        except User.DoesNotExist:
            # Créer un nouvel utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_superuser=True,
                is_staff=True,
                is_active=True
            )
            logger.info(f"🆕 Nouveau super_utilisateur créé : {username}")
            return user
            
    except ValidationError as e:
        logger.error(f"❌ Erreur de validation lors de la création de l'utilisateur : {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création/récupération de l'utilisateur : {e}")
        return None