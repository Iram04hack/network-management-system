# Generated manually to fix missing columns
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0001_initial'),
    ]

    operations = [
        # Ajouter les colonnes manquantes à ServiceCheck
        migrations.RunSQL(
            "ALTER TABLE monitoring_servicecheck ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE monitoring_servicecheck DROP COLUMN IF EXISTS created_at;"
        ),
        migrations.RunSQL(
            "ALTER TABLE monitoring_servicecheck ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE monitoring_servicecheck DROP COLUMN IF EXISTS updated_at;"
        ),
    ]
