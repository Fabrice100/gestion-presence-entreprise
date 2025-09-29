"""
Configuration de l'interface d'administration Django pour l'application reports.

Ce module configure l'interface d'administration pour :
- SystemSettings : Gestion des paramètres système
- ReportTemplate : Gestion des modèles de rapports

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import SystemSettings, ReportTemplate


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le modèle SystemSettings."""
    
    list_display = [
        'key', 'value', 'setting_type_display', 'is_active', 'updated_by_name', 'updated_at'
    ]
    
    list_filter = ['setting_type', 'is_active', 'updated_at']
    search_fields = ['key', 'value', 'description']
    ordering = ['setting_type', 'key']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Paramètre', {
            'fields': ('key', 'value', 'setting_type', 'description', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def setting_type_display(self, obj):
        colors = {
            'general': 'blue',
            'attendance': 'green',
            'leave': 'orange',
            'notification': 'purple',
            'security': 'red'
        }
        color = colors.get(obj.setting_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_setting_type_display()
        )
    setting_type_display.short_description = "Type"
    
    def updated_by_name(self, obj):
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.username
        return "Système"
    updated_by_name.short_description = "Modifié par"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau paramètre
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le modèle ReportTemplate."""
    
    list_display = [
        'name', 'report_type_display', 'format_display', 'is_active', 'is_public', 'created_by_name'
    ]
    
    list_filter = ['report_type', 'format', 'is_active', 'is_public', 'created_at']
    search_fields = ['name', 'description', 'template_content']
    ordering = ['report_type', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'report_type', 'format', 'is_active', 'is_public')
        }),
        ('Modèle', {
            'fields': ('template_content',)
        }),
        ('Paramètres', {
            'fields': ('parameters',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def report_type_display(self, obj):
        colors = {
            'attendance': 'green',
            'leave': 'orange',
            'anomaly': 'red',
            'summary': 'blue',
            'custom': 'purple'
        }
        color = colors.get(obj.report_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_report_type_display()
        )
    report_type_display.short_description = "Type de rapport"
    
    def format_display(self, obj):
        icons = {
            'pdf': '📄',
            'excel': '📊',
            'csv': '📋',
            'html': '🌐'
        }
        icon = icons.get(obj.format, '📄')
        return format_html(
            '{} {}',
            icon, obj.get_format_display()
        )
    format_display.short_description = "Format"
    
    def created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return "Système"
    created_by_name.short_description = "Créé par"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nouveau modèle
            obj.created_by = request.user
        super().save_model(request, obj, form, change)