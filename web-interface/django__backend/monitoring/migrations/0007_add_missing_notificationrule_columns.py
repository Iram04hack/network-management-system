# Generated manually to fix missing columns in NotificationRule model
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0006_add_missing_notification_columns'),
    ]

    operations = [
        # Ajouter les colonnes manquantes à NotificationRule
        migrations.RunSQL(
            "ALTER TABLE monitoring_notificationrule ADD COLUMN IF NOT EXISTS severity_threshold varchar(20) DEFAULT 'medium';",
            reverse_sql="ALTER TABLE monitoring_notificationrule DROP COLUMN IF EXISTS severity_threshold;"
        ),
    ]
