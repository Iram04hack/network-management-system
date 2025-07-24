# Generated manually to fix AIModel schema
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0005_fix_command'),
    ]

    operations = [
        # Ajouter les colonnes manquantes au modèle AIModel
        migrations.AddField(
            model_name='aimodel',
            name='max_tokens',
            field=models.IntegerField(default=2048),
        ),
        migrations.AddField(
            model_name='aimodel',
            name='temperature',
            field=models.FloatField(default=0.7),
        ),
        migrations.AddField(
            model_name='aimodel',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='aimodel',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        # Modifier les champs existants pour correspondre au modèle
        migrations.AlterField(
            model_name='aimodel',
            name='api_key',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='aimodel',
            name='endpoint',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='aimodel',
            name='provider',
            field=models.CharField(choices=[('openai', 'OpenAI'), ('anthropic', 'Anthropic'), ('huggingface', 'HuggingFace'), ('local', 'Local Model')], max_length=20),
        ),
    ]
