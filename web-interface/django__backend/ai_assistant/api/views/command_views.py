"""
Vues pour les commandes.

Ce module contient les vues qui exposent les fonctionnalités
d'exécution de commandes via une API REST.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ai_assistant.domain.services import CommandService
from ai_assistant.domain.exceptions import CommandExecutionError, SecurityError
from ai_assistant.api.serializers import CommandRequestSerializer, CommandResultSerializer


class CommandView(APIView):
    """Vue pour exécuter des commandes."""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.command_service = CommandService()
    
    def post(self, request):
        """Exécute une commande."""
        serializer = CommandRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        command = serializer.validated_data['command']
        command_type = serializer.validated_data['command_type']
        
        try:
            # Exécuter la commande en fonction du type
            if command_type == 'shell':
                result = self.command_service.execute_shell_command(command)
            elif command_type == 'sql':
                database_path = serializer.validated_data.get('database_path', ':memory:')
                result = self.command_service.execute_sql_query(command, database_path)
            elif command_type == 'python':
                result = self.command_service.execute_python_code(command)
            else:
                return Response(
                    {"error": f"Type de commande non supporté: {command_type}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Sérialiser le résultat
            result_serializer = CommandResultSerializer(result)
            
            return Response(result_serializer.data)
        
        except SecurityError as e:
            return Response(
                {
                    "error": str(e),
                    "command": command,
                    "command_type": command_type,
                    "security_violation": True
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        except CommandExecutionError as e:
            return Response(
                {
                    "error": str(e),
                    "command": command,
                    "command_type": command_type
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        except Exception as e:
            return Response(
                {
                    "error": f"Erreur lors de l'exécution de la commande: {str(e)}",
                    "command": command,
                    "command_type": command_type
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 