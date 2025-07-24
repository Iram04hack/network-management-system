# Generated manually to fix missing columns in DeviceServiceCheck model
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0002_add_missing_columns'),
    ]

    operations = [
        # Ajouter les colonnes manquantes à DeviceServiceCheck
        migrations.RunSQL(
            "ALTER TABLE monitoring_deviceservicecheck ADD COLUMN IF NOT EXISTS last_status varchar(50) DEFAULT 'unknown';",
            reverse_sql="ALTER TABLE monitoring_deviceservicecheck DROP COLUMN IF EXISTS last_status;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_deviceservicecheck ADD COLUMN IF NOT EXISTS last_check_output text;",
            reverse_sql="ALTER TABLE monitoring_deviceservicecheck DROP COLUMN IF EXISTS last_check_output;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_deviceservicecheck ADD COLUMN IF NOT EXISTS current_check_attempt integer DEFAULT 0;",
            reverse_sql="ALTER TABLE monitoring_deviceservicecheck DROP COLUMN IF EXISTS current_check_attempt;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_deviceservicecheck ADD COLUMN IF NOT EXISTS notification_enabled boolean DEFAULT true;",
            reverse_sql="ALTER TABLE monitoring_deviceservicecheck DROP COLUMN IF EXISTS notification_enabled;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_deviceservicecheck ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE monitoring_deviceservicecheck DROP COLUMN IF EXISTS created_at;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_deviceservicecheck ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE monitoring_deviceservicecheck DROP COLUMN IF EXISTS updated_at;"
        ),
    ]
