# Generated manually to fix missing columns in Report model
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0003_add_remaining_columns'),
    ]

    operations = [
        # Ajouter les colonnes manquantes à Report
        migrations.RunSQL(
            "ALTER TABLE reporting_report ADD COLUMN IF NOT EXISTS parameters jsonb DEFAULT '{}';",
            reverse_sql="ALTER TABLE reporting_report DROP COLUMN IF EXISTS parameters;"
        ),
        migrations.RunSQL(
            "ALTER TABLE reporting_report ADD COLUMN IF NOT EXISTS file_path varchar(255);",
            reverse_sql="ALTER TABLE reporting_report DROP COLUMN IF EXISTS file_path;"
        ),
    ]
