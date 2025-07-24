# Generated manually to fix missing columns in Dashboard model
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0007_add_missing_notificationrule_columns'),
    ]

    operations = [
        # Ajouter les colonnes manquantes à Dashboard
        migrations.RunSQL(
            "ALTER TABLE monitoring_dashboard ADD COLUMN IF NOT EXISTS is_public boolean DEFAULT false;",
            reverse_sql="ALTER TABLE monitoring_dashboard DROP COLUMN IF EXISTS is_public;"
        ),
    ]
