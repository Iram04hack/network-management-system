# Generated manually to fix the last 2 missing columns
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0010_add_final_missing_columns'),
    ]

    operations = [
        # Ajouter les 2 dernières colonnes manquantes
        migrations.RunSQL(
            "ALTER TABLE monitoring_alert ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}';",
            reverse_sql="ALTER TABLE monitoring_alert DROP COLUMN IF EXISTS metadata;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_notification ADD COLUMN IF NOT EXISTS action_text varchar(100);",
            reverse_sql="ALTER TABLE monitoring_notification DROP COLUMN IF EXISTS action_text;"
        ),
    ]
