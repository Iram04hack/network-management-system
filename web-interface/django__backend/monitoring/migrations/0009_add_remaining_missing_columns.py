# Generated manually to fix remaining missing columns
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0008_add_missing_dashboard_columns'),
    ]

    operations = [
        # Ajouter les colonnes manquantes à Alert
        migrations.RunSQL(
            "ALTER TABLE monitoring_alert ADD COLUMN IF NOT EXISTS resolved_by_id integer;",
            reverse_sql="ALTER TABLE monitoring_alert DROP COLUMN IF EXISTS resolved_by_id;"
        ),
        
        # Ajouter les colonnes manquantes à DeviceMetric
        migrations.RunSQL(
            "ALTER TABLE monitoring_devicemetric ADD COLUMN IF NOT EXISTS next_collection timestamp with time zone;",
            reverse_sql="ALTER TABLE monitoring_devicemetric DROP COLUMN IF EXISTS next_collection;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_devicemetric ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE monitoring_devicemetric DROP COLUMN IF EXISTS created_at;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_devicemetric ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE monitoring_devicemetric DROP COLUMN IF EXISTS updated_at;"
        ),
        
        # Ajouter les colonnes manquantes à Notification
        migrations.RunSQL(
            "ALTER TABLE monitoring_notification ADD COLUMN IF NOT EXISTS device_id bigint;",
            reverse_sql="ALTER TABLE monitoring_notification DROP COLUMN IF EXISTS device_id;"
        ),
        
        # Ajouter les colonnes manquantes à NotificationRule
        migrations.RunSQL(
            "ALTER TABLE monitoring_notificationrule ADD COLUMN IF NOT EXISTS quiet_period integer DEFAULT 300;",
            reverse_sql="ALTER TABLE monitoring_notificationrule DROP COLUMN IF EXISTS quiet_period;"
        ),
        
        # Ajouter les colonnes manquantes à Dashboard
        migrations.RunSQL(
            "ALTER TABLE monitoring_dashboard ADD COLUMN IF NOT EXISTS category varchar(50) DEFAULT 'general';",
            reverse_sql="ALTER TABLE monitoring_dashboard DROP COLUMN IF EXISTS category;"
        ),
        
        # Ajouter les contraintes de clé étrangère
        migrations.RunSQL(
            """
            ALTER TABLE monitoring_alert 
            ADD CONSTRAINT monitoring_alert_resolved_by_id_fkey 
            FOREIGN KEY (resolved_by_id) REFERENCES auth_user(id) ON DELETE SET NULL;
            """,
            reverse_sql="ALTER TABLE monitoring_alert DROP CONSTRAINT IF EXISTS monitoring_alert_resolved_by_id_fkey;"
        ),
        migrations.RunSQL(
            """
            ALTER TABLE monitoring_notification 
            ADD CONSTRAINT monitoring_notification_device_id_fkey 
            FOREIGN KEY (device_id) REFERENCES network_management_networkdevice(id) ON DELETE SET NULL;
            """,
            reverse_sql="ALTER TABLE monitoring_notification DROP CONSTRAINT IF EXISTS monitoring_notification_device_id_fkey;"
        ),
    ]
