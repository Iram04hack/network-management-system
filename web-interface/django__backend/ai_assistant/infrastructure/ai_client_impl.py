"""
Implémentations concrètes du client IA.

Ce module contient l'implémentation de l'interface AIClient pour interagir
avec différents services d'IA externes.
"""

from typing import Dict, Any, List, Optional, Generator, Callable
import logging
import time
import json
import requests
import os
import hashlib
import functools
from django.conf import settings
from django.core.cache import cache

from ..domain.interfaces import AIClient
from ..domain.exceptions import AIClientException

# Importation tardive pour éviter les dépendances circulaires
# AIModel sera importé à l'exécution des méthodes qui en ont besoin

logger = logging.getLogger(__name__)

# Configuration du cache
CACHE_TIMEOUT = getattr(settings, 'AI_ASSISTANT_CACHE_TIMEOUT', 3600)  # 1 heure par défaut
CACHE_ENABLED = getattr(settings, 'AI_ASSISTANT_CACHE_ENABLED', True)


def cache_response(func):
    """
    Décorateur pour mettre en cache les réponses du client IA.
    
    Args:
        func: Fonction à décorer
        
    Returns:
        Fonction décorée avec mise en cache
    """
    @functools.wraps(func)
    def wrapper(self, message, context=None, *args, **kwargs):
        if not CACHE_ENABLED:
            return func(self, message, context, *args, **kwargs)
        
        # Générer une clé de cache basée sur le message et le contexte
        cache_key = self._generate_cache_key(message, context)
        
        # Vérifier si la réponse est dans le cache
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.debug(f"Réponse récupérée du cache pour la clé: {cache_key}")
            return cached_result
        
        # Exécuter la fonction originale
        result = func(self, message, context, *args, **kwargs)
        
        # Stocker le résultat dans le cache
        cache.set(cache_key, result, CACHE_TIMEOUT)
        
        return result
    
    return wrapper


class DefaultAIClient(AIClient):
    """
    Implémentation par défaut du client IA.
    
    Cette classe fournit une implémentation concrète de l'interface AIClient,
    permettant d'interagir avec différents services d'IA comme OpenAI, assistants génériques, etc.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialise le client IA avec un modèle spécifique.
        
        Args:
            model_name: Nom du modèle à utiliser (optionnel)
        """
        self.model_name = model_name
        self.model_config = None
        self._load_model_config()
    
    def _load_model_config(self):
        """Charge la configuration du modèle depuis la base de données."""
        try:
            # Import tardif pour éviter les dépendances circulaires
            from ai_assistant.models import AIModel
            
            if self.model_name:
                self.model_config = AIModel.objects.filter(name=self.model_name, is_active=True).first()
            else:
                self.model_config = AIModel.objects.filter(is_active=True).first()
            
            if not self.model_config:
                logger.warning("Aucun modèle IA actif trouvé. Utilisation des paramètres par défaut.")
                
                # Utiliser les paramètres d'environnement si disponibles
                if hasattr(settings, 'DEFAULT_AI_PROVIDER'):
                    provider = settings.DEFAULT_AI_PROVIDER
                else:
                    provider = os.environ.get('AI_PROVIDER', 'openai')
                
                if hasattr(settings, 'DEFAULT_AI_MODEL'):
                    model = settings.DEFAULT_AI_MODEL
                else:
                    model = os.environ.get('AI_MODEL', 'gpt-3.5-turbo')
                
                if hasattr(settings, 'DEFAULT_AI_API_KEY'):
                    api_key = settings.DEFAULT_AI_API_KEY
                else:
                    api_key = os.environ.get('AI_API_KEY', '')
                
                # Créer un modèle par défaut
                self.model_config = AIModel(
                    name=model,
                    provider=provider,
                    model_name=model,
                    api_key=api_key,
                    is_active=True,
                    parameters={
                        'temperature': 0.7,
                        'max_tokens': 1000,
                        'system_message': "Tu es un assistant IA spécialisé dans la gestion de réseaux informatiques."
                    }
                )
                
                # Enregistrer le modèle par défaut si aucun modèle actif n'existe
                if not AIModel.objects.filter(is_active=True).exists():
                    try:
                        self.model_config.save()
                        logger.info(f"Modèle par défaut créé: {model}")
                    except Exception as e:
                        logger.error(f"Erreur lors de la création du modèle par défaut: {e}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration du modèle: {e}")
            raise AIClientException(f"Erreur de configuration: {e}", "config")
    
    def _generate_cache_key(self, message: str, context: List[str] = None) -> str:
        """
        Génère une clé de cache unique pour un message et son contexte.
        
        Args:
            message: Contenu du message
            context: Liste de messages précédents pour contexte
            
        Returns:
            Clé de cache unique
        """
        # Créer une représentation JSON du message et du contexte
        context_str = json.dumps(context) if context else "[]"
        model_name = getattr(self.model_config, 'name', 'default')
        
        # Générer un hash SHA-256 pour la clé de cache
        key_data = f"{model_name}:{message}:{context_str}"
        hash_obj = hashlib.sha256(key_data.encode('utf-8'))
        
        return f"ai_response:{hash_obj.hexdigest()}"
    
    @cache_response
    def generate_response(self, message: str, context: List[str] = None) -> Dict[str, Any]:
        """
        Génère une réponse à partir d'un message et d'un contexte.
        
        Args:
            message: Contenu du message
            context: Liste de messages précédents pour contexte
            
        Returns:
            Dictionnaire contenant la réponse générée
        """
        start_time = time.time()
        context = context or []
        
        try:
            # Vérifier si la configuration est valide
            if not self.model_config:
                raise AIClientException("Configuration du modèle manquante", "config")
            
            # Utilisation du fournisseur configuré
            provider = self.model_config.provider.lower() if hasattr(self.model_config, 'provider') else "openai"
            
            if provider == "openai":
                result = self._generate_openai_response(message, context)
            elif provider == "generic_ai":
                result = self._generate_generic_ai_response(message, context)
            elif provider == "huggingface":
                result = self._generate_huggingface_response(message, context)
            else:
                raise AIClientException(f"Fournisseur non supporté: {provider}", provider)
            
            # Calculer le temps de traitement
            processing_time = time.time() - start_time
            result["processing_time"] = round(processing_time, 2)
            
            return result
        except AIClientException as e:
            logger.exception(f"Erreur client IA: {e}")
            processing_time = time.time() - start_time
            
            return {
                "content": f"Erreur lors de la génération de la réponse: {str(e)}",
                "actions": [],
                "sources": [],
                "processing_time": round(processing_time, 2),
                "error": str(e)
            }
        except Exception as e:
            logger.exception(f"Erreur inattendue: {e}")
            processing_time = time.time() - start_time
            
            return {
                "content": f"Erreur lors de la génération de la réponse: {str(e)}",
                "actions": [],
                "sources": [],
                "processing_time": round(processing_time, 2),
                "error": str(e)
            }
    
    def generate_response_stream(self, message: str, context: List[str] = None, 
                                callback: Callable[[str], None] = None) -> Generator[str, None, Dict[str, Any]]:
        """
        Génère une réponse en streaming à partir d'un message et d'un contexte.
        
        Args:
            message: Contenu du message
            context: Liste de messages précédents pour contexte
            callback: Fonction de rappel pour traiter chaque fragment de réponse
            
        Yields:
            Fragments de la réponse générée
            
        Returns:
            Dictionnaire contenant la réponse complète générée
        """
        start_time = time.time()
        context = context or []
        full_content = ""
        
        try:
            # Vérifier si la configuration est valide
            if not self.model_config:
                raise AIClientException("Configuration du modèle manquante", "config")
            
            # Utilisation du fournisseur configuré
            provider = self.model_config.provider.lower() if hasattr(self.model_config, 'provider') else "openai"
            
            if provider == "openai":
                # Générer la réponse en streaming
                for chunk in self._generate_openai_response_stream(message, context):
                    if callback:
                        callback(chunk)
                    full_content += chunk
                    yield chunk
                
                # Extraire les actions et sources du contenu complet
                actions = self._extract_actions_from_content(full_content)
                sources = []  # À implémenter si nécessaire
                
                result = {
                    "content": full_content,
                    "actions": actions,
                    "sources": sources
                }
            else:
                # Pour les autres fournisseurs, utiliser la méthode non-streaming
                result = self.generate_response(message, context)
                if callback:
                    callback(result["content"])
                yield result["content"]
        
        except Exception as e:
            logger.exception(f"Erreur lors du streaming: {e}")
            error_message = f"Erreur lors de la génération de la réponse: {str(e)}"
            if callback:
                callback(error_message)
            yield error_message
            
            result = {
                "content": error_message,
                "actions": [],
                "sources": [],
                "error": str(e)
            }
        
        # Calculer le temps de traitement
        processing_time = time.time() - start_time
        result["processing_time"] = round(processing_time, 2)
        
        return result
    
    def analyze_command(self, command: str) -> Dict[str, Any]:
        """
        Analyse une commande pour déterminer sa validité et son intention.
        
        Args:
            command: La commande à analyser
            
        Returns:
            Dictionnaire avec l'analyse de la commande
        """
        try:
            # Vérification simple pour les commandes dangereuses
            dangerous_keywords = ["delete all", "remove all", "reset", "format"]
            for keyword in dangerous_keywords:
                if keyword in command.lower():
                    return {
                        "is_valid": False,
                        "safety_level": "dangerous",
                        "intent": "unknown",
                        "reason": f"Commande contenant un mot-clé dangereux: '{keyword}'"
                    }
            
            # Analyse basique de l'intention
            if "show" in command.lower() or "display" in command.lower() or "list" in command.lower():
                intent = "query"
            elif "create" in command.lower() or "add" in command.lower() or "insert" in command.lower():
                intent = "create"
            elif "update" in command.lower() or "modify" in command.lower() or "change" in command.lower():
                intent = "update"
            elif "delete" in command.lower() or "remove" in command.lower():
                intent = "delete"
            else:
                intent = "other"
            
            # Utiliser l'IA pour une analyse plus précise si disponible
            if self.model_config and hasattr(self.model_config, 'api_key') and self.model_config.api_key:
                try:
                    provider = self.model_config.provider.lower()
                    if provider == "openai":
                        ai_analysis = self._analyze_command_with_openai(command)
                        if ai_analysis:
                            return ai_analysis
                except Exception as e:
                    logger.warning(f"Erreur lors de l'analyse IA de la commande: {e}")
            
            # Analyse par défaut
            return {
                "is_valid": True,
                "safety_level": "safe",
                "intent": intent,
                "reason": ""
            }
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse de la commande: {e}")
            return {
                "is_valid": False,
                "safety_level": "unknown",
                "intent": "unknown",
                "reason": f"Erreur d'analyse: {str(e)}"
            }
    
    def _generate_openai_response(self, message: str, context: List[str]) -> Dict[str, Any]:
        """
        Génère une réponse via l'API OpenAI.
        
        Args:
            message: Message de l'utilisateur
            context: Liste des messages précédents pour contexte
            
        Returns:
            Dictionnaire contenant la réponse générée
        """
        try:
            # Vérification de la configuration
            if not hasattr(self.model_config, 'api_key') or not self.model_config.api_key:
                raise AIClientException("Clé API OpenAI manquante dans la configuration", "openai")
            
            # Importation de la bibliothèque OpenAI
            try:
                from openai import OpenAI
            except ImportError:
                raise AIClientException("La bibliothèque OpenAI n'est pas installée", "openai")
            
            # Initialisation du client OpenAI avec la nouvelle API v1.0+
            client_params = {'api_key': self.model_config.api_key}
            
            # Utiliser l'endpoint personnalisé si défini
            if hasattr(self.model_config, 'endpoint') and self.model_config.endpoint:
                client_params['base_url'] = self.model_config.endpoint
                
            client = OpenAI(**client_params)
            
            # Préparation des messages pour le format ChatCompletion
            messages = []
            
            # Ajouter le message système si disponible
            if hasattr(self.model_config, 'parameters'):
                system_message = self.model_config.parameters.get('system_message', '')
                if system_message:
                    messages.append({"role": "system", "content": system_message})
            
            # Ajouter les messages de contexte
            for i, ctx_msg in enumerate(context):
                role = "assistant" if i % 2 == 1 else "user"
                messages.append({"role": role, "content": ctx_msg})
            
            # Ajouter le message actuel
            messages.append({"role": "user", "content": message})
            
            # Récupérer les paramètres du modèle
            params = {}
            if hasattr(self.model_config, 'parameters'):
                params = self.model_config.parameters.copy() if self.model_config.parameters else {}
            
            # Préparer les paramètres pour l'appel API
            completion_params = {
                "model": self.model_config.model_name,
                "messages": messages,
                "temperature": params.get('temperature', 0.7),
                "max_tokens": params.get('max_tokens', 1000)
            }
            
            # Appel à l'API OpenAI
            response = client.chat.completions.create(**completion_params)
            
            # Extraction du contenu de la réponse
            content = response.choices[0].message.content
            
            # Extraction des actions du contenu
            actions = self._extract_actions_from_content(content)
            
            return {
                "content": content,
                "actions": actions,
                "sources": []
            }
        except Exception as e:
            logger.exception(f"Erreur lors de l'appel à l'API OpenAI: {e}")
            raise AIClientException(f"Erreur OpenAI: {e}", "openai") from e
    
    def _generate_openai_response_stream(self, message: str, context: List[str]) -> Generator[str, None, None]:
        """
        Génère une réponse en streaming via l'API OpenAI.
        
        Args:
            message: Message de l'utilisateur
            context: Liste des messages précédents pour contexte
            
        Yields:
            Fragments de la réponse générée
        """
        try:
            # Vérification de la configuration
            if not hasattr(self.model_config, 'api_key') or not self.model_config.api_key:
                raise AIClientException("Clé API OpenAI manquante dans la configuration", "openai")
            
            # Importation de la bibliothèque OpenAI
            try:
                from openai import OpenAI
            except ImportError:
                raise AIClientException("La bibliothèque OpenAI n'est pas installée", "openai")
            
            # Initialisation du client OpenAI avec la nouvelle API v1.0+
            client_params = {'api_key': self.model_config.api_key}
            
            # Utiliser l'endpoint personnalisé si défini
            if hasattr(self.model_config, 'endpoint') and self.model_config.endpoint:
                client_params['base_url'] = self.model_config.endpoint
                
            client = OpenAI(**client_params)
            
            # Préparation des messages pour le format ChatCompletion
            messages = []
            
            # Ajouter le message système si disponible
            if hasattr(self.model_config, 'parameters'):
                system_message = self.model_config.parameters.get('system_message', '')
                if system_message:
                    messages.append({"role": "system", "content": system_message})
            
            # Ajouter les messages de contexte
            for i, ctx_msg in enumerate(context):
                role = "assistant" if i % 2 == 1 else "user"
                messages.append({"role": role, "content": ctx_msg})
            
            # Ajouter le message actuel
            messages.append({"role": "user", "content": message})
            
            # Récupérer les paramètres du modèle
            params = {}
            if hasattr(self.model_config, 'parameters'):
                params = self.model_config.parameters.copy() if self.model_config.parameters else {}
            
            # Préparer les paramètres pour l'appel API
            completion_params = {
                "model": self.model_config.model_name,
                "messages": messages,
                "temperature": params.get('temperature', 0.7),
                "max_tokens": params.get('max_tokens', 1000),
                "stream": True  # Activer le streaming
            }
            
            # Appel à l'API OpenAI avec streaming
            stream = client.chat.completions.create(**completion_params)
            
            # Traiter chaque fragment de la réponse
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.exception(f"Erreur lors du streaming OpenAI: {e}")
            raise AIClientException(f"Erreur OpenAI: {e}", "openai") from e
    
    def _extract_actions_from_content(self, content: str) -> List[Dict[str, Any]]:
        """
        Extrait les actions du contenu de la réponse.
        
        Args:
            content: Contenu de la réponse
            
        Returns:
            Liste des actions extraites
        """
        actions = []
        
        # Recherche des actions au format [ACTION:type:paramètres]
        import re
        action_pattern = r'\[ACTION:(\w+):([^\]]+)\]'
        matches = re.findall(action_pattern, content)
        
        for action_type, params_str in matches:
            try:
                # Essayer de parser les paramètres comme du JSON
                params = json.loads(params_str)
            except json.JSONDecodeError:
                # Fallback: utiliser les paramètres comme une chaîne
                params = params_str
                
            actions.append({
                "type": action_type,
                "parameters": params
            })
        
        return actions
    
    def _generate_generic_ai_response(self, message: str, context: List[str]) -> Dict[str, Any]:
        """
        Génère une réponse via une API d'IA générique.
        
        Args:
            message: Message de l'utilisateur
            context: Liste des messages précédents pour contexte
            
        Returns:
            Dictionnaire contenant la réponse générée
        """
        try:
            # Vérification de la configuration
            if not hasattr(self.model_config, 'api_key') or not self.model_config.api_key:
                raise AIClientException("Clé API manquante dans la configuration", "generic_ai")
            
            # Importation de la bibliothèque générique d'IA
            try:
                import requests
            except ImportError:
                raise AIClientException("La bibliothèque requests n'est pas installée", "generic_ai")
            
            # Configuration pour API générique
            api_url = getattr(self.model_config, 'endpoint', 'http://localhost:8080/v1/chat/completions')
            headers = {
                'Authorization': f'Bearer {self.model_config.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Préparation des messages pour le format Anthropic
            messages = []
            
            # Conversion du contexte en format de messages Anthropic
            for ctx_msg in context:
                if ctx_msg.startswith("user: "):
                    messages.append({"role": "user", "content": ctx_msg[6:]})
                elif ctx_msg.startswith("assistant: "):
                    messages.append({"role": "assistant", "content": ctx_msg[11:]})
                elif ctx_msg.startswith("system: "):
                    # Anthropic utilise un paramètre system séparé, on le stocke pour l'instant
                    system_content = ctx_msg[8:]
            
            # Ajout du message actuel
            messages.append({"role": "user", "content": message})
            
            # Récupération des paramètres du modèle
            model_params = self.model_config.parameters or {}
            temperature = model_params.get('temperature', 0.7)
            max_tokens = model_params.get('max_tokens', 1000)
            
            # Système message par défaut si non trouvé dans le contexte
            system_message = next((ctx_msg[8:] for ctx_msg in context if ctx_msg.startswith("system: ")), 
                "Tu es un assistant IA spécialisé dans la gestion de réseaux informatiques.")
            
            # Appel à l'API générique
            logger.info(f"Appel à l'API générique avec le modèle {self.model_config.model_name}")
            
            payload = {
                'model': self.model_config.model_name,
                'messages': [{'role': 'system', 'content': system_message}] + messages,
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            response_data = response.json()
            
            # Extraction du contenu de la réponse
            content = response_data['choices'][0]['message']['content']
            
            # Extraction des actions potentielles du contenu
            actions = self._extract_actions_from_content(content)
            
            # Construction du résultat
            return {
                "content": content,
                "actions": actions,
                "sources": [],
                "model_info": {
                    "provider": "generic_ai",
                    "model": self.model_config.model_name,
                    "tokens_used": response_data.get('usage', {}).get('total_tokens', 0)
                }
            }
        except ImportError:
            raise AIClientException("La bibliothèque requests n'est pas installée", "generic_ai")
        except Exception as e:
            raise AIClientException(f"Erreur lors de l'appel à l'API générique: {e}", "generic_ai")
    
    def _generate_huggingface_response(self, message: str, context: List[str]) -> Dict[str, Any]:
        """
        Génère une réponse via l'API HuggingFace.
        
        Args:
            message: Message de l'utilisateur
            context: Liste des messages précédents pour contexte
            
        Returns:
            Dictionnaire contenant la réponse générée
        """
        try:
            # Vérification de la configuration
            if not hasattr(self.model_config, 'api_key') or not self.model_config.api_key:
                raise AIClientException("Clé API HuggingFace manquante dans la configuration", "huggingface")
            
            # Importation des bibliothèques nécessaires
            try:
                import requests
                from huggingface_hub import InferenceClient
            except ImportError:
                raise AIClientException("Les bibliothèques HuggingFace ne sont pas installées", "huggingface")
            
            # Initialisation du client HuggingFace
            client = InferenceClient(token=self.model_config.api_key)
            
            # Préparation du prompt avec le contexte
            prompt = ""
            
            # Ajout du contexte système si disponible
            system_message = next((ctx_msg[8:] for ctx_msg in context if ctx_msg.startswith("system: ")),
                "Tu es un assistant IA spécialisé dans la gestion de réseaux informatiques.")
            prompt += f"Instructions système: {system_message}\n\n"
            
            # Ajout des messages précédents
            for ctx_msg in context:
                if ctx_msg.startswith("user: "):
                    prompt += f"Utilisateur: {ctx_msg[6:]}\n"
                elif ctx_msg.startswith("assistant: "):
                    prompt += f"Assistant: {ctx_msg[11:]}\n"
            
            # Ajout du message actuel
            prompt += f"Utilisateur: {message}\nAssistant:"
            
            # Récupération des paramètres du modèle
            model_params = self.model_config.parameters or {}
            temperature = model_params.get('temperature', 0.7)
            max_tokens = model_params.get('max_tokens', 1000)
            
            # Détermination du modèle à utiliser
            model_id = self.model_config.model_name
            
            # Appel à l'API HuggingFace
            logger.info(f"Appel à l'API HuggingFace avec le modèle {model_id}")
            
            # Utilisation de l'API Text Generation
            response = client.text_generation(
                prompt,
                model=model_id,
                temperature=temperature,
                max_new_tokens=max_tokens,
                do_sample=True
            )
            
            # Extraction du contenu de la réponse
            content = response.strip()
            
            # Extraction des actions potentielles du contenu
            actions = self._extract_actions_from_content(content)
            
            # Construction du résultat
            return {
                "content": content,
                "actions": actions,
                "sources": [],
                "model_info": {
                    "provider": "huggingface",
                    "model": model_id,
                    "tokens_used": None  # HuggingFace ne retourne pas toujours cette information
                }
            }
        except ImportError:
            raise AIClientException("Les bibliothèques HuggingFace ne sont pas installées", "huggingface")
        except Exception as e:
            raise AIClientException(f"Erreur lors de l'appel à l'API HuggingFace: {e}", "huggingface")
    
    def _analyze_command_with_openai(self, command: str) -> Dict[str, Any]:
        """
        Utilise OpenAI pour analyser une commande.
        
        Args:
            command: La commande à analyser
            
        Returns:
            Résultat de l'analyse ou None en cas d'échec
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.model_config.api_key)
            
            prompt = f"""
            Analyse la commande suivante et détermine:
            1. Si elle est valide (is_valid: true/false)
            2. Son niveau de sécurité (safety_level: "safe", "warning", "dangerous")
            3. Son intention (intent: "query", "create", "update", "delete", "other")
            4. Une raison pour l'analyse (reason: explication)
            
            Commande: "{command}"
            
            Réponds uniquement au format JSON.
            """
            
            response = client.chat.completions.create(
                model=self.model_config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            
            # Extraction du JSON
            try:
                # Trouver le début et la fin du JSON
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    result = json.loads(json_str)
                    
                    # Vérifier les clés requises
                    required_keys = ["is_valid", "safety_level", "intent", "reason"]
                    if all(key in result for key in required_keys):
                        return result
            except json.JSONDecodeError:
                logger.warning("Erreur de décodage JSON dans la réponse d'analyse de commande")
            
            return None
        except Exception as e:
            logger.warning(f"Erreur lors de l'analyse de commande avec OpenAI: {e}")
            return None 