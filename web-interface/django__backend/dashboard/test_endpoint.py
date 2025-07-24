"""
Endpoint temporaire pour tester que l'erreur execute a été corrigée
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import asyncio
from .di_container import container

@csrf_exempt
@require_http_methods(["GET"])
def test_dashboard_fix(request):
    """Endpoint temporaire pour démontrer la correction de l'erreur execute"""
    
    try:
        # Test du service dashboard
        dashboard_service = container.get_service('dashboard_service')
        
        async def test_service():
            result = await dashboard_service.get_dashboard_overview(user_id=1)
            return {
                'success': True,
                'message': 'Dashboard service is working correctly',
                'error_fixed': "'DashboardDataServiceImpl' object has no attribute 'execute' - RESOLVED",
                'result_type': str(type(result)),
                'sample_data': {
                    'devices': result.devices,
                    'alerts_count': len(result.security_alerts) + len(result.system_alerts),
                    'health_overall': result.health_metrics.get_overall_status().value
                }
            }
        
        result = asyncio.run(test_service())
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)