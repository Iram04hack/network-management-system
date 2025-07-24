# Generated manually to fix missing columns
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0001_initial'),
    ]

    operations = [
        # Ajouter les colonnes manquantes à ScheduledReport
        migrations.RunSQL(
            "ALTER TABLE reporting_scheduledreport ADD COLUMN IF NOT EXISTS next_run timestamp with time zone;",
            reverse_sql="ALTER TABLE reporting_scheduledreport DROP COLUMN IF EXISTS next_run;"
        ),
        migrations.RunSQL(
            "ALTER TABLE reporting_scheduledreport ADD COLUMN IF NOT EXISTS last_run timestamp with time zone;",
            reverse_sql="ALTER TABLE reporting_scheduledreport DROP COLUMN IF EXISTS last_run;"
        ),
        migrations.RunSQL(
            "ALTER TABLE reporting_scheduledreport ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE reporting_scheduledreport DROP COLUMN IF EXISTS created_at;"
        ),
        migrations.RunSQL(
            "ALTER TABLE reporting_scheduledreport ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE reporting_scheduledreport DROP COLUMN IF EXISTS updated_at;"
        ),
        migrations.RunSQL(
            "ALTER TABLE reporting_scheduledreport ADD COLUMN IF NOT EXISTS parameters jsonb DEFAULT '{}';",
            reverse_sql="ALTER TABLE reporting_scheduledreport DROP COLUMN IF EXISTS parameters;"
        ),
        migrations.RunSQL(
            "ALTER TABLE reporting_scheduledreport ADD COLUMN IF NOT EXISTS format varchar(10) DEFAULT 'pdf';",
            reverse_sql="ALTER TABLE reporting_scheduledreport DROP COLUMN IF EXISTS format;"
        ),

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
