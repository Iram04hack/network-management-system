"""
Gestionnaires de signaux pour le module Dashboard.

Ce fichier contient les gestionnaires de signaux Django qui réagissent
aux événements du système pour mettre à jour le tableau de bord.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import UserDashboardConfig, DashboardWidget, DashboardPreset

logger = logging.getLogger(__name__)

# Modèle utilisateur
User = get_user_model()


@receiver(post_save, sender=User)
def create_user_dashboard_config(sender, instance, created, **kwargs):
    """
    Crée une configuration de tableau de bord par défaut pour les nouveaux utilisateurs.
    
    Args:
        sender: Classe du modèle qui a envoyé le signal
        instance: Instance de l'utilisateur créé
        created: Booléen indiquant si l'instance a été créée
    """
    if created:
        try:
            # Récupérer le preset par défaut
            try:
                default_preset = DashboardPreset.objects.get(is_default=True)
                preset_exists = True
            except (DashboardPreset.DoesNotExist, DashboardPreset.MultipleObjectsReturned):
                preset_exists = False
            
            # Créer la configuration utilisateur
            user_config = UserDashboardConfig.objects.create(
                user=instance,
                theme=default_preset.theme if preset_exists else "light",
                layout=default_preset.layout if preset_exists else "grid",
                refresh_interval=default_preset.refresh_interval if preset_exists else 60
            )
            
            # Si un preset par défaut existe, copier ses widgets
            if preset_exists:
                for preset_widget in default_preset.widgets.all():
                    DashboardWidget.objects.create(
                        config=user_config,
                        widget_type=preset_widget.widget_type,
                        position_x=preset_widget.position_x,
                        position_y=preset_widget.position_y,
                        width=preset_widget.width,
                        height=preset_widget.height,
                        settings=preset_widget.settings
                    )
            else:
                # Créer des widgets par défaut
                DashboardWidget.objects.create(
                    config=user_config,
                    widget_type="system_health",
                    position_x=0,
                    position_y=0,
                    width=4,
                    height=2,
                    settings={}
                )
                
                DashboardWidget.objects.create(
                    config=user_config,
                    widget_type="alerts",
                    position_x=0,
                    position_y=2,
                    width=8,
                    height=3,
                    settings={"limit": 5}
                )
            
            logger.info(f"Configuration de tableau de bord créée pour l'utilisateur {instance.username}")
        except Exception as e:
            logger.error(f"Erreur lors de la création de la configuration de tableau de bord: {e}")


@receiver(post_delete, sender=UserDashboardConfig)
def cleanup_dashboard_widgets(sender, instance, **kwargs):
    """
    Nettoie les widgets associés à une configuration supprimée.
    
    Args:
        sender: Classe du modèle qui a envoyé le signal
        instance: Instance de la configuration supprimée
    """
    try:
        # Les widgets devraient être supprimés automatiquement par la relation CASCADE,
        # mais on peut effectuer d'autres nettoyages si nécessaire
        logger.info(f"Configuration de tableau de bord supprimée pour l'utilisateur {instance.user_id}")
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des widgets: {e}")


# Autres gestionnaires de signaux pour réagir aux événements système
# Par exemple, pour mettre à jour le tableau de bord lorsque des alertes sont créées 