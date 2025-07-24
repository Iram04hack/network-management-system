# Generated manually to fix missing columns in Alert model
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0003_add_deviceservicecheck_columns'),
    ]

    operations = [
        # Ajouter les colonnes manquantes à Alert
        migrations.RunSQL(
            "ALTER TABLE monitoring_alert ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE monitoring_alert DROP COLUMN IF EXISTS created_at;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_alert ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE monitoring_alert DROP COLUMN IF EXISTS updated_at;"
        ),
    ]
