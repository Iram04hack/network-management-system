# Generated manually to fix missing columns in Notification model
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0005_add_missing_metricsdefinition_columns'),
    ]

    operations = [
        # Ajouter les colonnes manquantes à Notification
        migrations.RunSQL(
            "ALTER TABLE monitoring_notification ADD COLUMN IF NOT EXISTS alert_id bigint;",
            reverse_sql="ALTER TABLE monitoring_notification DROP COLUMN IF EXISTS alert_id;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_notification ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE monitoring_notification DROP COLUMN IF EXISTS updated_at;"
        ),
        
        # Ajouter la contrainte de clé étrangère pour alert_id
        migrations.RunSQL(
            """
            ALTER TABLE monitoring_notification 
            ADD CONSTRAINT monitoring_notification_alert_id_fkey 
            FOREIGN KEY (alert_id) REFERENCES monitoring_alert(id) ON DELETE SET NULL;
            """,
            reverse_sql="ALTER TABLE monitoring_notification DROP CONSTRAINT IF EXISTS monitoring_notification_alert_id_fkey;"
        ),
    ]
