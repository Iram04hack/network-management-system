# Contenu pour reporting/models.py
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class Report(models.Model):
    """Modèle pour les rapports"""
    
    REPORT_TYPES = [
        ('network', 'Network Report'),
        ('security', 'Security Report'),
        ('performance', 'Performance Report'),
        ('audit', 'Audit Report'),
        ('custom', 'Custom Report'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    title = models.CharField(max_length=255, default="Rapport")
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    template = models.ForeignKey('ReportTemplate', on_delete=models.SET_NULL, null=True, related_name='reports')
    status = models.CharField(max_length=20, default='draft', choices=STATUS_CHOICES)
    content = models.JSONField(default=dict, blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    file_path = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        app_label = 'reporting'
    
    def __str__(self):
        return self.title

class ReportTemplate(models.Model):
    """Modèle pour les templates de rapport"""
    
    TEMPLATE_TYPES = [
        ('network_status', 'Network Status'),
        ('security_audit', 'Security Audit'),
        ('performance', 'Performance'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES)
    content = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        app_label = 'reporting'
    
    def __str__(self):
        return self.name

class ScheduledReport(models.Model):
    """Modèle pour les rapports programmés"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('html', 'HTML'),
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='schedules', null=True)
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='schedules', null=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    is_active = models.BooleanField(default=True)
    recipients = models.ManyToManyField(User, related_name='scheduled_reports')
    start_date = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    last_run = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parameters = models.JSONField(default=dict, blank=True)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    
    class Meta:
        app_label = 'reporting'
    
    def __str__(self):
        report_title = self.report.title if self.report else "Rapport non défini"
        return f"{report_title} ({self.frequency})"
