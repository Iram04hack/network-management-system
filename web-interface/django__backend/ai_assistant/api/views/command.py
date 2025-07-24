"""
Vues API pour l'exécution de commandes.

Ce module contient les vues API pour exécuter des commandes shell,
SQL ou Python et récupérer leurs résultats.
"""

import time
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ai_assistant.api.serializers import (
    CommandRequestSerializer,
    CommandResponseSerializer,
    ErrorResponseSerializer,
)
from ai_assistant.domain.services import CommandService, ConversationService
from ai_assistant.domain.exceptions import (
    CommandExecutionError,
    ValidationError,
    SecurityError,
)

logger = logging.getLogger(__name__)


class CommandExecutionView(APIView):
    """Vue pour exécuter des commandes."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_service = CommandService()
        self.conversation_service = ConversationService()
    
    def post(self, request):
        """
        Exécute une commande et renvoie son résultat.
        
        Args:
            request: Requête HTTP
            
        Returns:
            Response: Réponse HTTP contenant le résultat de la commande
        """
        # Valider la requête
        serializer = CommandRequestSerializer(data=request.data)
        if not serializer.is_valid():
            error_serializer = ErrorResponseSerializer({
                'error': "Données invalides",
                'error_type': 'ValidationError',
                'detail': serializer.errors,
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_id = str(request.user.id)
            command = serializer.validated_data['command']
            command_type = serializer.validated_data.get('command_type', 'shell')
            conversation_id = serializer.validated_data.get('conversation_id')
            
            # Vérifier si la commande est sécurisée
            safety_analysis = self.command_service.analyze_command_safety(command, command_type)
            if not safety_analysis.get('is_safe', False):
                error_serializer = ErrorResponseSerializer({
                    'error': "Commande potentiellement dangereuse",
                    'error_type': 'SecurityError',
                    'detail': safety_analysis.get('reason', "La commande a été bloquée pour des raisons de sécurité"),
                    'status_code': 403
                })
                return Response(error_serializer.data, status=status.HTTP_403_FORBIDDEN)
            
            # Exécuter la commande
            start_time = time.time()
            
            if command_type == 'shell':
                result = self.command_service.execute_shell_command(command)
            elif command_type == 'sql':
                result = self.command_service.execute_sql_query(command)
            elif command_type == 'python':
                result = self.command_service.execute_python_code(command)
            else:
                raise ValidationError(f"Type de commande non supporté: {command_type}")
            
            execution_time = time.time() - start_time
            
            # Si un ID de conversation est fourni, enregistrer la commande et son résultat
            if conversation_id:
                # Ajouter la commande comme message utilisateur
                self.conversation_service.add_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=f"```{command_type}\n{command}\n```",
                    metadata={
                        'command_type': command_type,
                        'is_command': True
                    }
                )
                
                # Ajouter le résultat comme message assistant
                result_content = f"```\n{result.stdout}\n```" if result.success else f"```\nErreur: {result.stderr}\n```"
                self.conversation_service.add_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=result_content,
                    metadata={
                        'command_result': {
                            'exit_code': result.exit_code,
                            'success': result.success,
                            'execution_time': execution_time
                        }
                    }
                )
            
            # Préparer la réponse
            response_data = {
                'success': result.success,
                'output': result.stdout,
                'error': result.stderr,
                'exit_code': result.exit_code,
                'execution_time': execution_time,
                'safety_analysis': safety_analysis
            }
            
            # Sérialiser la réponse
            response_serializer = CommandResponseSerializer(response_data)
            
            return Response(response_serializer.data)
        
        except SecurityError as e:
            logger.warning(f"Erreur de sécurité: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'SecurityError',
                'status_code': 403
            })
            return Response(error_serializer.data, status=status.HTTP_403_FORBIDDEN)
        
        except CommandExecutionError as e:
            logger.error(f"Erreur d'exécution de commande: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'CommandExecutionError',
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except ValidationError as e:
            logger.warning(f"Erreur de validation: {str(e)}")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': 'ValidationError',
                'status_code': 400
            })
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception("Erreur lors de l'exécution de la commande")
            error_serializer = ErrorResponseSerializer({
                'error': str(e),
                'error_type': e.__class__.__name__,
                'status_code': 500
            })
            return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 