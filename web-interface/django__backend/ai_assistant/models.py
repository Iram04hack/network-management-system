from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import json
import uuid


class AIModel(models.Model):
    """Configuration des modèles IA disponibles"""
    
    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('huggingface', 'HuggingFace'),
        ('local', 'Local Model'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    model_name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    endpoint = models.URLField(blank=True, null=True)
    capabilities = models.JSONField(default=dict)
    max_tokens = models.IntegerField(default=2048)
    temperature = models.FloatField(default=0.7)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'ai_assistant'
        db_table = 'ai_assistant_aimodel'
        verbose_name = _('AI Model')
        verbose_name_plural = _('AI Models')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.provider} - {self.model_name}"


class Conversation(models.Model):
    """Conversations avec l'assistant IA"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='ai_conversations'
    )
    title = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = 'ai_assistant'
        db_table = 'ai_assistant_conversation'
        verbose_name = _('Conversation')
        verbose_name_plural = _('Conversations')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation {self.id} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.title and self.messages.exists():
            first_message = self.messages.filter(role='user').first()
            if first_message:
                self.title = first_message.content[:50] + '...' if len(first_message.content) > 50 else first_message.content
        super().save(*args, **kwargs)


class Message(models.Model):
    """Messages dans les conversations"""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    model_used = models.ForeignKey(
        AIModel, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    processing_time = models.FloatField(null=True, blank=True)
    token_count = models.IntegerField(null=True, blank=True)
    actions_taken = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = 'ai_assistant'
        db_table = 'ai_assistant_message'
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role} - {self.content[:50]}..."


class KnowledgeBase(models.Model):
    """Base de connaissances pour l'assistant"""

    CATEGORY_CHOICES = [
        ('network', 'Network'),
        ('security', 'Security'),
        ('troubleshooting', 'Troubleshooting'),
        ('configuration', 'Configuration'),
        ('monitoring', 'Monitoring'),
        ('general', 'General'),
    ]

    # Champs pour compatibilité avec l'API documents
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    content_type = models.CharField(max_length=100, default='text/plain')
    tags = models.JSONField(default=list, blank=True)

    # Champs originaux
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    question = models.TextField(blank=True)
    answer = models.TextField(blank=True)
    keywords = models.JSONField(default=list)
    related_commands = models.JSONField(default=list)
    confidence_score = models.FloatField(default=1.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        app_label = 'ai_assistant'
        db_table = 'ai_assistant_knowledgebase'
        verbose_name = _('Knowledge Base Entry')
        verbose_name_plural = _('Knowledge Base Entries')
        ordering = ['-confidence_score', 'category']
    
    def __str__(self):
        return f"{self.category} - {self.question[:50]}..."


class Command(models.Model):
    """Commandes système disponibles pour l'assistant"""

    CATEGORY_CHOICES = [
        ('network', 'Network'),
        ('system', 'System'),
        ('monitoring', 'Monitoring'),
        ('security', 'Security'),
        ('configuration', 'Configuration'),
    ]

    PERMISSION_CHOICES = [
        ('read', 'Read Only'),
        ('write', 'Read/Write'),
        ('admin', 'Administrator'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    command_template = models.TextField()
    parameters = models.JSONField(default=dict)
    required_permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES)
    is_safe = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    timeout_seconds = models.IntegerField(default=30)

    # Champs pour l'exécution de commandes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'ai_assistant'
        db_table = 'ai_assistant_command'
        verbose_name = _('Command')
        verbose_name_plural = _('Commands')
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.category} - {self.name}"


class ConversationMetrics(models.Model):
    """Métriques des conversations pour analyse"""
    
    conversation = models.OneToOneField(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='metrics'
    )
    total_messages = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    average_response_time = models.FloatField(default=0.0)
    successful_commands = models.IntegerField(default=0)
    failed_commands = models.IntegerField(default=0)
    user_satisfaction_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'ai_assistant'
        db_table = 'ai_assistant_conversationmetrics'
        verbose_name = _('Conversation Metrics')
        verbose_name_plural = _('Conversation Metrics')
    
    def __str__(self):
        return f"Metrics for Conversation {self.conversation.id}"


class APIUsage(models.Model):
    """Suivi de l'utilisation des APIs IA"""
    
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_count = models.IntegerField(default=0)
    token_count = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'ai_assistant'
        db_table = 'ai_assistant_apiusage'
        verbose_name = _('API Usage')
        verbose_name_plural = _('API Usage')
        unique_together = ['model', 'user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user.username} - {self.model.name} - {self.date}"


class UserPreference(models.Model):
    """Préférences utilisateur pour l'assistant IA"""
    
    LANGUAGE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'English'),
        ('es', 'Español'),
        ('de', 'Deutsch'),
    ]
    
    RESPONSE_STYLE_CHOICES = [
        ('concise', 'Concise'),
        ('detailed', 'Detailed'),
        ('technical', 'Technical'),
        ('friendly', 'Friendly'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='ai_preferences'
    )
    
    # Préférences générales
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='fr')
    response_style = models.CharField(max_length=20, choices=RESPONSE_STYLE_CHOICES, default='detailed')
    max_conversation_length = models.IntegerField(default=100)
    enable_notifications = models.BooleanField(default=True)
    
    # Préférences IA
    preferred_model = models.ForeignKey(
        AIModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=2048)
    
    # Fonctionnalités activées
    enable_command_execution = models.BooleanField(default=False)
    enable_file_analysis = models.BooleanField(default=True)
    enable_code_generation = models.BooleanField(default=True)
    enable_network_analysis = models.BooleanField(default=True)
    
    # Préférences de sécurité
    require_confirmation_for_commands = models.BooleanField(default=True)
    allowed_command_categories = models.JSONField(default=list)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'ai_assistant'
        db_table = 'ai_assistant_userpreference'
        verbose_name = _('User Preference')
        verbose_name_plural = _('User Preferences')
    
    def __str__(self):
        return f"Preferences for {self.user.username}"