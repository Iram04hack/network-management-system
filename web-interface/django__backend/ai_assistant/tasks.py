"""
Tâches Celery pour le module AI Assistant
"""
import logging
import time
from datetime import timedelta, datetime
from typing import Dict, Any, List, Optional
import json

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.db.models import Avg, Count, F, Sum
from django.contrib.auth.models import User

from .models import Conversation, Message, KnowledgeBase, AIModel, Command, ConversationMetrics, APIUsage

logger = logging.getLogger(__name__)

@shared_task
def cleanup_old_conversations(days=30):
    """Nettoie les conversations inactives depuis plus de X jours."""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        old_conversations = Conversation.objects.filter(updated_at__lt=cutoff_date)
        count = old_conversations.count()
        
        if count > 0:
            # Option 1: Suppression physique avec nettoyage des métriques
            metrics_to_delete = ConversationMetrics.objects.filter(conversation__in=old_conversations)
            metrics_count = metrics_to_delete.count()
            metrics_to_delete.delete()
            
            # Option 2: Archivage (marquer comme inactives)
            old_conversations.update(is_active=False)
            
            logger.info(f"Nettoyage terminé: {count} conversations archivées, {metrics_count} métriques supprimées (inactives depuis {days} jours)")
        else:
            logger.info(f"Aucune conversation à nettoyer (inactives depuis {days} jours)")
        
        return {"status": "success", "archived_count": count}
    except Exception as e:
        logger.exception(f"Erreur lors du nettoyage des conversations: {e}")
        return {"status": "error", "error": str(e)}

@shared_task
def update_knowledge_base_usage():
    """Met à jour les statistiques d'utilisation de la base de connaissances."""
    logger.info("Début de la mise à jour des statistiques de la base de connaissances")
    
    try:
        # Période de calcul (dernière semaine)
        one_week_ago = datetime.now() - timedelta(days=7)
        
        updated_count = 0
        for kb_entry in KnowledgeBase.objects.all():
            # Compter les utilisations dans les métadonnées des messages
            usage_count = Message.objects.filter(
                created_at__gte=one_week_ago,
                metadata__contains={'knowledge_base_used': kb_entry.id}
            ).count()
            
            if usage_count != kb_entry.usage_count:
                kb_entry.usage_count = usage_count
                kb_entry.save(update_fields=['usage_count'])
                updated_count += 1
        
        logger.info(f"Mise à jour terminée: {updated_count} entrées de base de connaissances mises à jour")
        return {
            "success": True,
            "updated": updated_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des statistiques KB: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@shared_task
def generate_daily_summary() -> Dict[str, Any]:
    """Génère un résumé quotidien des interactions avec l'assistant IA."""
    logger.info("Début de la génération du résumé quotidien")
    
    try:
        # Calculer la période
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        # Récupérer les données
        conversations = Conversation.objects.filter(
            created_at__range=(start_date, end_date)
        )
        
        messages = Message.objects.filter(
            timestamp__range=(start_date, end_date)
        )
        
        # Calculer les statistiques
        total_conversations = conversations.count()
        total_messages = messages.count()
        avg_messages_per_conv = total_messages / total_conversations if total_conversations > 0 else 0
        
        user_messages = messages.filter(role='user').count()
        assistant_messages = messages.filter(role='assistant').count()
        
        # Statistiques par modèle
        model_usage = messages.filter(
            role='assistant',
            model_used__isnull=False
        ).values('model_used__name', 'model_used__provider').annotate(
            count=Count('id'),
            avg_processing_time=Avg('processing_time'),
            total_tokens=Sum('token_count')
        )
        
        # Commandes les plus utilisées
        popular_commands = []
        for message in messages.filter(role='assistant'):
            actions = message.actions_taken
            if actions:
                for action in actions:
                    if isinstance(action, dict) and action.get('type') == 'command':
                        popular_commands.append(action.get('command', 'unknown'))
        
        # Générer le rapport
        summary = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "statistics": {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "avg_messages_per_conversation": round(avg_messages_per_conv, 2),
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "response_ratio": round(assistant_messages / user_messages, 2) if user_messages > 0 else 0
            },
            "model_usage": list(model_usage),
            "popular_commands": list(set(popular_commands))[:10]  # Top 10
        }
        
        # Stocker dans le cache
        cache.set('ai_assistant_daily_summary', summary, 86400)  # 24h
        
        logger.info(f"Résumé généré: {total_conversations} conversations, {total_messages} messages")
        return {
            "success": True,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de la génération du résumé: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@shared_task
def update_conversation_metrics():
    """Met à jour les métriques des conversations actives."""
    try:
        # Compter les conversations actives des 24 dernières heures
        one_day_ago = datetime.now() - timedelta(days=1)
        active_count = Conversation.objects.filter(
            updated_at__gte=one_day_ago,
            is_active=True
        ).count()
        
        # Calculer d'autres métriques
        total_active_conversations = Conversation.objects.filter(is_active=True).count()
        avg_messages_per_conversation = ConversationMetrics.objects.aggregate(
            avg=Avg('total_messages')
        )['avg'] or 0
        
        # Stocker dans le cache pour l'API de santé
        metrics = {
            'active_conversations_24h': active_count,
            'total_active_conversations': total_active_conversations,
            'avg_messages_per_conversation': round(avg_messages_per_conversation, 2),
            'last_updated': datetime.now().isoformat()
        }
        
        cache.set('ai_assistant_conversation_metrics', metrics, 3600)
        
        logger.info(f"Métriques de conversations mises à jour: {active_count} conversations actives (24h)")
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        logger.exception(f"Erreur lors de la mise à jour des métriques de conversations: {e}")
        return {"status": "error", "error": str(e)}

@shared_task
def collect_api_usage_metrics():
    """Collecte des métriques sur l'utilisation des APIs IA."""
    try:
        # Période de collecte (dernières 24h)
        one_day_ago = datetime.now().date() - timedelta(days=1)
        
        # Agréger les données par modèle et utilisateur
        usage_data = APIUsage.objects.filter(
            date=one_day_ago
        ).values(
            'model__name', 
            'model__provider'
        ).annotate(
            total_requests=Sum('request_count'),
            total_tokens=Sum('token_count'),
            total_cost=Sum('cost'),
            unique_users=Count('user', distinct=True)
        )
        
        results = []
        total_cost = 0
        total_tokens = 0
        total_requests = 0
        
        for usage in usage_data:
            model_name = usage.get('model__name') or 'unknown'
            provider = usage.get('model__provider') or 'unknown'
            requests = usage.get('total_requests') or 0
            tokens = usage.get('total_tokens') or 0
            cost = float(usage.get('total_cost') or 0)
            users = usage.get('unique_users') or 0
            
            results.append({
                'model': model_name,
                'provider': provider,
                'requests': requests,
                'tokens': tokens,
                'cost': cost,
                'unique_users': users
            })
            
            total_cost += cost
            total_tokens += tokens
            total_requests += requests
        
        # Stocker le résumé global
        summary = {
            'date': one_day_ago.isoformat(),
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'total_cost': round(total_cost, 6),
            'models': results,
            'collected_at': datetime.now().isoformat()
        }
        
        cache.set('ai_assistant_api_usage_summary', summary, 86400)  # 24h
        
        logger.info(f"Métriques d'utilisation API collectées: {len(results)} modèles, {total_requests} requêtes")
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.exception(f"Erreur lors de la collecte des métriques d'utilisation API: {e}")
        return {"status": "error", "error": str(e)}

@shared_task
def check_ai_services_health():
    """Vérifie la santé des services IA."""
    try:
        # Vérifier la base de données
        db_status = "healthy"
        db_details = {}
        try:
            # Test simple de requête
            start_time = time.time()
            count = Conversation.objects.count()
            latency = time.time() - start_time
            
            db_details = {
                "latency": round(latency, 3),
                "total_conversations": count
            }
        except Exception as e:
            db_status = "unhealthy"
            db_details = {"error": str(e)}
        
        # Vérifier les modèles IA actifs
        ai_models_status = "healthy"
        ai_models_details = {}
        try:
            active_models = AIModel.objects.filter(is_active=True).count()
            total_models = AIModel.objects.count()
            
            ai_models_details = {
                "active_models": active_models,
                "total_models": total_models,
                "availability_ratio": round(active_models / total_models, 2) if total_models > 0 else 0
            }
            
            if active_models == 0:
                ai_models_status = "unhealthy"
                ai_models_details["warning"] = "Aucun modèle IA actif"
                
        except Exception as e:
            ai_models_status = "unhealthy"
            ai_models_details = {"error": str(e)}
        
        # Vérifier les métriques récentes
        metrics_status = "healthy"
        metrics_details = {}
        try:
            # Vérifier si on a des messages récents (dernière heure)
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_messages = Message.objects.filter(timestamp__gte=one_hour_ago).count()
            
            metrics_details = {
                "recent_messages_1h": recent_messages,
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            metrics_status = "degraded"
            metrics_details = {"error": str(e)}
        
        # Construire le rapport de santé complet
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy" if all(
                s == "healthy" for s in [db_status, ai_models_status, metrics_status]
            ) else "degraded",
            "services": {
                "database": {
                    "status": db_status,
                    "details": db_details
                },
                "ai_models": {
                    "status": ai_models_status,
                    "details": ai_models_details
                },
                "metrics": {
                    "status": metrics_status,
                    "details": metrics_details
                }
            }
        }
        
        # Stocker dans le cache pour l'API de santé
        cache.set('ai_assistant_health_report', health_report, 300)  # 5 minutes
        
        logger.info(f"Vérification de santé des services IA: {health_report['overall_status']}")
        return {"status": "success", "health_report": health_report}
    except Exception as e:
        logger.exception(f"Erreur lors de la vérification de santé des services IA: {e}")
        error_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "error",
            "error": str(e)
        }
        cache.set('ai_assistant_health_report', error_report, 300)
        return {"status": "error", "error": str(e)}

@shared_task
def optimize_conversation_performance():
    """Optimise les performances des conversations."""
    try:
        optimized_count = 0
        
        # Identifier les conversations avec beaucoup de messages
        heavy_conversations = Conversation.objects.annotate(
            message_count=Count('messages')
        ).filter(message_count__gt=100, is_active=True)
        
        for conversation in heavy_conversations:
            # Archiver les anciens messages (garder les 50 derniers)
            old_messages = conversation.messages.order_by('-timestamp')[50:]
            archived_count = old_messages.count()
            
            if archived_count > 0:
                # Mettre à jour les métadonnées pour indiquer l'archivage
                conversation.metadata = conversation.metadata or {}
                conversation.metadata['archived_messages'] = conversation.metadata.get('archived_messages', 0) + archived_count
                conversation.save()
                
                optimized_count += 1
                logger.info(f"Conversation {conversation.id}: {archived_count} messages archivés")
        
        logger.info(f"Optimisation terminée: {optimized_count} conversations optimisées")
        return {
            "status": "success",
            "optimized_conversations": optimized_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.exception(f"Erreur lors de l'optimisation des performances: {e}")
        return {"status": "error", "error": str(e)}

@shared_task 
def rotate_api_keys():
    """Tâche pour la rotation des clés API (si nécessaire)."""
    try:
        # Cette tâche pourrait être utilisée pour faire la rotation des clés API
        # automatiquement si votre infrastructure le supporte
        
        models_to_rotate = AIModel.objects.filter(
            is_active=True,
            api_key__isnull=False
        )
        
        rotated_count = 0
        for model in models_to_rotate:
            # Logique de rotation des clés (à implémenter selon vos besoins)
            # Par exemple, récupérer une nouvelle clé depuis un service de gestion de secrets
            pass
        
        logger.info(f"Rotation des clés API: {rotated_count} clés mises à jour")
        return {
            "status": "success", 
            "rotated_keys": rotated_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.exception(f"Erreur lors de la rotation des clés API: {e}")
        return {"status": "error", "error": str(e)}

# Configuration pour Celery Beat (à ajouter dans settings.py)
"""
CELERY_BEAT_SCHEDULE = {
    'update-conversation-metrics': {
        'task': 'ai_assistant.tasks.update_conversation_metrics',
        'schedule': crontab(minute=0),  # Toutes les heures
    },
    'collect-api-usage-metrics': {
        'task': 'ai_assistant.tasks.collect_api_usage_metrics', 
        'schedule': crontab(hour=0, minute=30),  # Tous les jours à 00:30
    },
    'check-ai-services-health': {
        'task': 'ai_assistant.tasks.check_ai_services_health',
        'schedule': crontab(minute='*/15'),  # Toutes les 15 minutes
    },
    'cleanup-old-conversations': {
        'task': 'ai_assistant.tasks.cleanup_old_conversations',
        'schedule': crontab(hour=1, minute=0),  # Tous les jours à 01:00
    },
    'generate-daily-summary': {
        'task': 'ai_assistant.tasks.generate_daily_summary',
        'schedule': crontab(hour=6, minute=0),  # Tous les jours à 06:00
    },
    'update-knowledge-base-usage': {
        'task': 'ai_assistant.tasks.update_knowledge_base_usage',
        'schedule': crontab(hour=2, minute=0, day_of_week=1),  # Tous les lundis à 02:00
    },
    'optimize-conversation-performance': {
        'task': 'ai_assistant.tasks.optimize_conversation_performance',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Tous les dimanches à 03:00
    },
}
"""