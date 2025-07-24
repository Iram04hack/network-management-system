# Generated manually to fix final missing columns
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0009_add_remaining_missing_columns'),
    ]

    operations = [
        # Ajouter les colonnes manquantes finales à Alert
        migrations.RunSQL(
            "ALTER TABLE monitoring_alert ADD COLUMN IF NOT EXISTS acknowledgement_comment text;",
            reverse_sql="ALTER TABLE monitoring_alert DROP COLUMN IF EXISTS acknowledgement_comment;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_alert ADD COLUMN IF NOT EXISTS resolution_comment text;",
            reverse_sql="ALTER TABLE monitoring_alert DROP COLUMN IF EXISTS resolution_comment;"
        ),
        
        # Ajouter les colonnes manquantes finales à DeviceMetric
        migrations.RunSQL(
            "ALTER TABLE monitoring_devicemetric ADD COLUMN IF NOT EXISTS custom_parameters jsonb;",
            reverse_sql="ALTER TABLE monitoring_devicemetric DROP COLUMN IF EXISTS custom_parameters;"
        ),
        
        # Ajouter les colonnes manquantes finales à Notification
        migrations.RunSQL(
            "ALTER TABLE monitoring_notification ADD COLUMN IF NOT EXISTS action_url varchar(255);",
            reverse_sql="ALTER TABLE monitoring_notification DROP COLUMN IF EXISTS action_url;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_notification ADD COLUMN IF NOT EXISTS action_label varchar(100);",
            reverse_sql="ALTER TABLE monitoring_notification DROP COLUMN IF EXISTS action_label;"
        ),
    ]
