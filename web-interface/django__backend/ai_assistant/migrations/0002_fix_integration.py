# Generated manually for Phase 1 integration fixes

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0001_initial'),
    ]

    operations = [
        # Ajouter les champs manquants au modèle KnowledgeBase
        migrations.AddField(
            model_name='knowledgebase',
            name='title',
            field=models.CharField(max_length=255, blank=True, default=''),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='content',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='content_type',
            field=models.CharField(max_length=100, default='text/plain'),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='tags',
            field=models.JSONField(default=list, blank=True),
        ),
        
        # Ajouter les champs manquants au modèle Command
        migrations.AddField(
            model_name='command',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('pending', 'Pending'),
                    ('running', 'Running'),
                    ('completed', 'Completed'),
                    ('failed', 'Failed'),
                ],
                default='pending'
            ),
        ),
        migrations.AddField(
            model_name='command',
            name='result',
            field=models.JSONField(default=dict, blank=True),
        ),
        migrations.AddField(
            model_name='command',
            name='metadata',
            field=models.JSONField(default=dict, blank=True),
        ),
        
        # Modifier le champ category de KnowledgeBase pour avoir une valeur par défaut
        migrations.AlterField(
            model_name='knowledgebase',
            name='category',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('network', 'Network'),
                    ('security', 'Security'),
                    ('troubleshooting', 'Troubleshooting'),
                    ('configuration', 'Configuration'),
                    ('monitoring', 'Monitoring'),
                    ('general', 'General'),
                ],
                default='general'
            ),
        ),
        
        # Rendre les champs question et answer optionnels
        migrations.AlterField(
            model_name='knowledgebase',
            name='question',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='knowledgebase',
            name='answer',
            field=models.TextField(blank=True, default=''),
        ),
    ]
