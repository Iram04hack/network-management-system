# Generated manually to fix missing columns in MetricsDefinition model
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0004_add_missing_alert_columns'),
    ]

    operations = [
        # Ajouter les colonnes manquantes à MetricsDefinition
        migrations.RunSQL(
            "ALTER TABLE monitoring_metricsdefinition ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE monitoring_metricsdefinition DROP COLUMN IF EXISTS created_at;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_metricsdefinition ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE monitoring_metricsdefinition DROP COLUMN IF EXISTS updated_at;"
        ),
    ]
