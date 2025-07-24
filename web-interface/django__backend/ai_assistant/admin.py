from django.contrib import admin
from .models import (
    AIModel,
    Conversation,
    Message,
    KnowledgeBase,
    Command,
    ConversationMetrics,
    APIUsage,
    UserPreference
)


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'model_name', 'is_active')
    list_filter = ('provider', 'is_active')
    search_fields = ('name', 'model_name')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'user__username')
    date_hierarchy = 'created_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'created_at', 'token_count')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'conversation__title')
    date_hierarchy = 'created_at'


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'question', 'confidence_score', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')


@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'required_permission', 'is_safe', 'is_active')
    list_filter = ('category', 'required_permission', 'is_safe', 'is_active')
    search_fields = ('name', 'description', 'command_template')


@admin.register(ConversationMetrics)
class ConversationMetricsAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'total_messages', 'total_tokens', 'average_response_time')
    list_filter = ('created_at',)
    search_fields = ('conversation__title',)


@admin.register(APIUsage)
class APIUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'model', 'date', 'request_count', 'token_count', 'cost')
    list_filter = ('date', 'model')
    search_fields = ('user__username',)
    date_hierarchy = 'date'


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'language', 'response_style', 'preferred_model', 'enable_notifications', 'created_at')
    list_filter = ('language', 'response_style', 'enable_notifications', 'enable_command_execution')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Préférences de langue et style', {
            'fields': ('language', 'response_style', 'preferred_model')
        }),
        ('Paramètres de conversation', {
            'fields': ('max_conversation_length', 'temperature', 'max_tokens')
        }),
        ('Autorisations et sécurité', {
            'fields': ('enable_command_execution', 'enable_file_analysis', 'enable_code_generation', 'enable_network_analysis', 'require_confirmation_for_commands', 'allowed_command_categories')
        }),
        ('Notifications', {
            'fields': ('enable_notifications',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    ) 