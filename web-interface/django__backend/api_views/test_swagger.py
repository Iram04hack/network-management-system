"""
Test simple pour vérifier que Swagger fonctionne
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method='get',
    operation_summary="Test API simple",
    operation_description="API de test pour vérifier que Swagger fonctionne",
    responses={
        200: openapi.Response(
            description="Test réussi",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description="Statut"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message"),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, description="Horodatage"),
                }
            )
        )
    },
    tags=['views']
)
@api_view(['GET'])
def test_api(request):
    """API de test simple"""
    from django.utils import timezone
    return JsonResponse({
        'status': 'success',
        'message': 'Swagger fonctionne correctement !',
        'timestamp': timezone.now().isoformat(),
        'api_views_module': 'operational'
    })