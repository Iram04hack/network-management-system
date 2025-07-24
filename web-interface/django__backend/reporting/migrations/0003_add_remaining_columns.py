# Generated manually to fix remaining missing columns
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0002_add_missing_columns'),
    ]

    operations = [
        # Ajouter les colonnes manquantes à Report
        migrations.RunSQL(
            "ALTER TABLE reporting_report ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE reporting_report DROP COLUMN IF EXISTS updated_at;"
        ),
        
        # Ajouter les colonnes manquantes à ReportTemplate
        migrations.RunSQL(
            "ALTER TABLE reporting_reporttemplate ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE reporting_reporttemplate DROP COLUMN IF EXISTS updated_at;"
        ),
    ]
