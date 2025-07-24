# nms_backend/middleware.py
import uuid
import logging
import traceback
from django.http import JsonResponse
from django.conf import settings
from common.domain.exceptions import NMSException

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            # Si c'est une exception NMS, elle est déjà gérée par notre middleware spécialisé
            if isinstance(e, NMSException):
                # Laisser le middleware ExceptionHandlerMiddleware gérer cette exception
                raise
                
            # Générer un identifiant unique pour cette erreur
            error_id = str(uuid.uuid4())
            
            # Journaliser l'erreur avec les détails
            logger.error(
                f"Exception non gérée [{error_id}]: {e}",
                exc_info=True,
                extra={
                    'error_id': error_id,
                    'path': request.path,
                    'method': request.method,
                    'user_id': request.user.id if request.user.is_authenticated else None
                }
            )
            
            # En mode debug, inclure le traceback complet
            if settings.DEBUG:
                error_details = {
                    'error': True,
                    'code': 'server_error',
                    'message': str(e),
                    'error_id': error_id,
                    'details': {
                        'traceback': traceback.format_exc().splitlines()
                    }
                }
            else:
                # En production, n'exposer que l'ID de l'erreur
                error_details = {
                    'error': True,
                    'code': 'server_error',
                    'message': 'Une erreur système est survenue',
                    'error_id': error_id
                }
            
            return JsonResponse(error_details, status=500)
