# Generated manually to create the missing Alert table
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('network_management', '0006_add_missing_networkinterface_columns'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Titre')),
                ('message', models.TextField(verbose_name='Message')),
                ('severity', models.CharField(default='medium', max_length=50, verbose_name='Sévérité')),
                ('status', models.CharField(default='active', max_length=50, verbose_name='Statut')),
                ('source', models.CharField(max_length=100, verbose_name='Source')),
                ('category', models.CharField(max_length=100, verbose_name='Catégorie')),
                ('details', models.JSONField(blank=True, null=True, verbose_name='Détails')),
                ('acknowledged', models.BooleanField(default=False, verbose_name='Acquittée')),
                ('acknowledged_by', models.CharField(blank=True, max_length=255, verbose_name='Acquittée par')),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True, verbose_name="Date d'acquittement")),
                ('acknowledgement_comment', models.TextField(blank=True, verbose_name="Commentaire d'acquittement")),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('device', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='network_alerts', to='network_management.networkdevice', verbose_name='Équipement')),
                ('interface', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='network_management.networkinterface', verbose_name='Interface')),
            ],
            options={
                'verbose_name': 'Alerte',
                'verbose_name_plural': 'Alertes',
                'ordering': ['-created_at'],
            },
        ),
    ]
