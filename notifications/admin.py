"""
Configuration de l'interface d'administration pour les notifications.

Ce module configure l'interface d'administration Django pour :
- Gestion des templates d'emails
- Visualisation des notifications
- Configuration des paramètres

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Notification, EmailTemplate, NotificationSettings
from .services import EmailTemplateService


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Administration des notifications.
    """
    
    list_display = [
        'user', 'title', 'notification_type', 'priority', 
        'is_read', 'is_sent', 'created_at'
    ]
    
    list_filter = [
        'notification_type', 'priority', 'is_read', 'is_sent', 'created_at'
    ]
    
    search_fields = ['user__username', 'user__email', 'title', 'message']
    
    readonly_fields = ['created_at', 'read_at']
    
    fieldsets = (
        ('Notification', {
            'fields': ('user', 'title', 'message', 'notification_type', 'priority')
        }),
        ('Action', {
            'fields': ('action_url', 'action_text')
        }),
        ('État', {
            'fields': ('is_read', 'is_sent', 'created_at', 'read_at')
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'send_email']
    
    def mark_as_read(self, request, queryset):
        """
        Marque les notifications sélectionnées comme lues.
        """
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} notifications marquées comme lues.')
    mark_as_read.short_description = "Marquer comme lues"
    
    def mark_as_unread(self, request, queryset):
        """
        Marque les notifications sélectionnées comme non lues.
        """
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} notifications marquées comme non lues.')
    mark_as_unread.short_description = "Marquer comme non lues"
    
    def send_email(self, request, queryset):
        """
        Envoie les notifications par email.
        """
        sent_count = 0
        for notification in queryset:
            if notification.send_email():
                sent_count += 1
        
        self.message_user(request, f'{sent_count} emails envoyés avec succès.')
    send_email.short_description = "Envoyer par email"


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """
    Administration des templates d'emails.
    """
    
    list_display = [
        'name', 'template_type', 'is_active', 'created_at'
    ]
    
    list_filter = ['template_type', 'is_active', 'created_at']
    
    search_fields = ['name', 'template_type', 'subject']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'template_type', 'is_active')
        }),
        ('Contenu', {
            'fields': ('subject', 'html_content', 'text_content')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['create_default_templates']
    
    def create_default_templates(self, request, queryset):
        """
        Crée les templates par défaut.
        """
        created_count = EmailTemplateService.create_default_templates()
        self.message_user(request, f'{created_count} templates créés.')
    create_default_templates.short_description = "Créer les templates par défaut"


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    """
    Administration des paramètres de notifications.
    """
    
    list_display = [
        'user', 'email_notifications', 'email_frequency', 
        'leave_notifications', 'attendance_notifications'
    ]
    
    list_filter = [
        'email_notifications', 'email_frequency', 
        'leave_notifications', 'attendance_notifications',
        'system_notifications'
    ]
    
    search_fields = ['user__username', 'user__email']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Paramètres email', {
            'fields': ('email_notifications', 'email_frequency')
        }),
        ('Types de notifications', {
            'fields': ('leave_notifications', 'attendance_notifications', 'system_notifications')
        }),
        ('Heures silencieuses', {
            'fields': ('quiet_hours_start', 'quiet_hours_end')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
    )
