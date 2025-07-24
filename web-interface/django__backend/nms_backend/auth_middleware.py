"""
Middleware d'authentification transparente pour le Network Management System.

Ce middleware gère l'authentification transparente en créant automatiquement
un super_utilisateur Django lorsqu'un utilisateur se connecte via le frontend.
"""

import logging
import hashlib
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.conf import settings
import json

logger = logging.getLogger(__name__)


class TransparentAuthMiddleware:
    """
    Middleware qui gère l'authentification transparente.
    
    Lorsqu'un utilisateur se connecte via le frontend, ce middleware :
    1. Vérifie si l'utilisateur Django existe
    2. Crée automatiquement un super_utilisateur Django si nécessaire
    3. Authentifie l'utilisateur de manière transparente
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        logger.info("🔐 Middleware d'authentification transparente initialisé")
    
    def __call__(self, request):
        # Traiter la requête avant la vue
        response = self.process_request(request)
        if response:
            return response
        
        # Appeler la vue
        response = self.get_response(request)
        
        # Traiter la réponse après la vue
        return self.process_response(request, response)
    
    def process_request(self, request):
        """
        Traite la requête entrante pour gérer l'authentification transparente.
        """
        # Vérifier si c'est une requête d'authentification
        if request.path in ['/api/auth/login/', '/api/auth/transparent-login/']:
            return self.handle_transparent_auth(request)
        
        # Vérifier si c'est une requête API nécessitant une authentification
        # Temporairement désactivé pour le développement des APIs de monitoring
        if False and request.path.startswith('/api/') and not request.user.is_authenticated:
            return self.handle_api_auth(request)
        
        return None
    
    def handle_transparent_auth(self, request):
        """
        Gère l'authentification transparente lors de la connexion.
        """
        if request.method != 'POST':
            return None
        
        try:
            # Extraire les données de connexion
            if hasattr(request, 'body') and request.body:
                data = json.loads(request.body.decode('utf-8'))
            else:
                data = request.POST
            
            username = data.get('username')
            password = data.get('password')
            email = data.get('email', f"{username}@nms.local")
            
            if not username or not password:
                return JsonResponse({
                    'error': 'Nom d\'utilisateur et mot de passe requis',
                    'transparent_auth': False
                }, status=400)
            
            # Créer ou récupérer l'utilisateur Django
            user = self.get_or_create_superuser(username, email, password)
            
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
                    
                    return JsonResponse({
                        'success': True,
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'is_superuser': user.is_superuser,
                            'is_staff': user.is_staff,
                        },
                        'transparent_auth': True,
                        'message': 'Connexion réussie avec accès complet aux APIs'
                    })
                else:
                    logger.warning(f"❌ Échec d'authentification pour {username}")
                    return JsonResponse({
                        'error': 'Identifiants invalides',
                        'transparent_auth': False
                    }, status=401)
            else:
                return JsonResponse({
                    'error': 'Impossible de créer ou récupérer l\'utilisateur',
                    'transparent_auth': False
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Données JSON invalides',
                'transparent_auth': False
            }, status=400)
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'authentification transparente : {e}")
            return JsonResponse({
                'error': 'Erreur interne du serveur',
                'transparent_auth': False
            }, status=500)
    
    def handle_api_auth(self, request):
        """
        Gère l'authentification pour les requêtes API.
        """
        # Vérifier les headers d'authentification
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Basic '):
            try:
                import base64
                credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
                username, password = credentials.split(':', 1)
                
                # Essayer d'authentifier
                user = authenticate(request, username=username, password=password)
                if user:
                    login(request, user)
                    logger.debug(f"🔐 API auth réussie pour {username}")
                    return None
                else:
                    logger.warning(f"❌ API auth échouée pour {username}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'authentification API : {e}")
        
        # Retourner une erreur d'authentification si nécessaire
        # (laisser Django gérer par défaut)
        return None
    
    def get_or_create_superuser(self, username, email, password):
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
    
    def process_response(self, request, response):
        """
        Traite la réponse après la vue.
        """
        # Ajouter des headers de sécurité
        if request.path.startswith('/api/'):
            response['X-NMS-Auth'] = 'transparent'
            if request.user.is_authenticated:
                response['X-NMS-User'] = request.user.username
                response['X-NMS-Superuser'] = 'true' if request.user.is_superuser else 'false'
        
        return response


class APIAuthenticationMiddleware:
    """
    Middleware spécialisé pour l'authentification API.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        logger.info("🔐 Middleware d'authentification API initialisé")
    
    def __call__(self, request):
        # Traiter l'authentification API
        self.process_api_auth(request)
        
        # Appeler la vue
        response = self.get_response(request)
        
        return response
    
    def process_api_auth(self, request):
        """
        Traite l'authentification pour les requêtes API.
        """
        if not request.path.startswith('/api/'):
            return
        
        # Vérifier si l'utilisateur est déjà authentifié
        if request.user.is_authenticated:
            return
        
        # Vérifier les headers d'authentification Basic
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Basic '):
            try:
                import base64
                credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
                username, password = credentials.split(':', 1)
                
                # Authentifier l'utilisateur
                user = authenticate(request, username=username, password=password)
                if user:
                    login(request, user)
                    logger.debug(f"🔐 Authentification API réussie pour {username}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'authentification API : {e}")