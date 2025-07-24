# Generated manually to fix missing columns in NetworkInterface model
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('network_management', '0005_remove_networkdevice_contact_and_more'),
    ]

    operations = [
        # Ajouter les colonnes manquantes à NetworkInterface
        migrations.RunSQL(
            "ALTER TABLE network_management_networkinterface ADD COLUMN IF NOT EXISTS mtu integer;",
            reverse_sql="ALTER TABLE network_management_networkinterface DROP COLUMN IF EXISTS mtu;"
        ),
        migrations.RunSQL(
            "ALTER TABLE network_management_networkinterface ADD COLUMN IF NOT EXISTS extra_data jsonb;",
            reverse_sql="ALTER TABLE network_management_networkinterface DROP COLUMN IF EXISTS extra_data;"
        ),
        migrations.RunSQL(
            "ALTER TABLE network_management_networkinterface ADD COLUMN IF NOT EXISTS created_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE network_management_networkinterface DROP COLUMN IF EXISTS created_at;"
        ),
        migrations.RunSQL(
            "ALTER TABLE network_management_networkinterface ADD COLUMN IF NOT EXISTS updated_at timestamp with time zone DEFAULT NOW();",
            reverse_sql="ALTER TABLE network_management_networkinterface DROP COLUMN IF EXISTS updated_at;"
        ),
        
        # Corriger le type de speed (doit être BigIntegerField)
        migrations.RunSQL(
            "ALTER TABLE network_management_networkinterface ALTER COLUMN speed TYPE bigint;",
            reverse_sql="ALTER TABLE network_management_networkinterface ALTER COLUMN speed TYPE integer;"
        ),
    ]
