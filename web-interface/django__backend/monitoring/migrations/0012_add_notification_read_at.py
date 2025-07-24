# Generated manually to fix the very last missing column
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0011_add_last_missing_columns'),
    ]

    operations = [
        # Ajouter les toutes dernières colonnes manquantes
        migrations.RunSQL(
            "ALTER TABLE monitoring_notification ADD COLUMN IF NOT EXISTS read_at timestamp with time zone;",
            reverse_sql="ALTER TABLE monitoring_notification DROP COLUMN IF EXISTS read_at;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_notification ADD COLUMN IF NOT EXISTS metadata jsonb DEFAULT '{}';",
            reverse_sql="ALTER TABLE monitoring_notification DROP COLUMN IF EXISTS metadata;"
        ),
    ]
