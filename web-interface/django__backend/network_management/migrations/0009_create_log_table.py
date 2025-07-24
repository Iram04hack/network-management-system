# Generated manually to create the missing Log table
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('network_management', '0008_create_metric_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(max_length=50, verbose_name='Niveau')),
                ('message', models.TextField(verbose_name='Message')),
                ('source', models.CharField(max_length=100, verbose_name='Source')),
                ('details', models.JSONField(blank=True, null=True, verbose_name='Détails')),
                ('timestamp', models.DateTimeField(verbose_name='Horodatage')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name="Date d'enregistrement")),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='network_management.networkdevice', verbose_name='Équipement')),
            ],
            options={
                'verbose_name': 'Log',
                'verbose_name_plural': 'Logs',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='log',
            index=models.Index(fields=['device', 'level', 'timestamp'], name='network_man_device_d4e5f6_idx'),
        ),
        migrations.AddIndex(
            model_name='log',
            index=models.Index(fields=['source', 'timestamp'], name='network_man_source_g7h8i9_idx'),
        ),
    ]
