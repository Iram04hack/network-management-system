# Generated manually to create the missing Metric table
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('network_management', '0007_create_alert_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='Metric',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('value', models.FloatField(verbose_name='Valeur')),
                ('unit', models.CharField(blank=True, max_length=50, verbose_name='Unité')),
                ('category', models.CharField(max_length=100, verbose_name='Catégorie')),
                ('tags', models.JSONField(blank=True, null=True, verbose_name='Tags')),
                ('timestamp', models.DateTimeField(verbose_name='Horodatage')),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='network_metrics', to='network_management.networkdevice', verbose_name='Équipement')),
                ('interface', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='network_metrics', to='network_management.networkinterface', verbose_name='Interface')),
            ],
            options={
                'verbose_name': 'Métrique',
                'verbose_name_plural': 'Métriques',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='metric',
            index=models.Index(fields=['device', 'name', 'timestamp'], name='network_man_device_b8e8e8_idx'),
        ),
        migrations.AddIndex(
            model_name='metric',
            index=models.Index(fields=['interface', 'name', 'timestamp'], name='network_man_interfa_a1b2c3_idx'),
        ),
    ]
