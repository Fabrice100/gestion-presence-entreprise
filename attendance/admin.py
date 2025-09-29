"""
Configuration de l'interface d'administration Django pour l'application attendance.

Ce module configure l'interface d'administration pour :
- Attendance : Gestion des pointages
- AttendanceAnomaly : Gestion des anomalies

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Attendance, AttendanceAnomaly


class AttendanceAnomalyInline(admin.TabularInline):
    """
    Inline admin pour afficher les anomalies d'un pointage.
    """
    model = AttendanceAnomaly
    extra = 0
    readonly_fields = ['anomaly_type', 'description', 'status', 'created_at']
    fields = ['anomaly_type', 'description', 'status', 'created_at']
    can_delete = False


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """
    Configuration de l'administration pour le modèle Attendance.
    """
    
    list_display = [
        'employee_name',
        'date',
        'time',
        'punch_type_display',
        'status_display',
        'distance_display',
        'accuracy_display',
        'source',
        'created_at'
    ]
    
    list_filter = [
        'punch_type',
        'status',
        'source',
        'date',
        'employee__employee_profile__department',
        'created_at'
    ]
    
    search_fields = [
        'employee__first_name',
        'employee__last_name',
        'employee__username',
        'employee__employee_profile__employee_id',
        'notes'
    ]
    
    ordering = ['-date', '-time']
    
    fieldsets = (
        ('Informations de pointage', {
            'fields': (
                'employee',
                'date',
                'time',
                'punch_type',
                'status'
            )
        }),
        ('Géolocalisation', {
            'fields': (
                'latitude',
                'longitude',
                'accuracy',
                'distance_from_site'
            )
        }),
        ('Informations techniques', {
            'fields': (
                'source',
                'user_agent',
                'ip_address'
            )
        }),
        ('Notes et commentaires', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['distance_from_site', 'created_at', 'updated_at']
    
    inlines = [AttendanceAnomalyInline]
    
    def employee_name(self, obj):
        """Affiche le nom de l'employé avec son ID."""
        try:
            profile = obj.employee.employee_profile
            return f"{obj.employee.get_full_name() or obj.employee.username} ({profile.employee_id})"
        except:
            return obj.employee.get_full_name() or obj.employee.username
    employee_name.short_description = "Employé"
    
    def punch_type_display(self, obj):
        """Affiche le type de pointage avec une couleur."""
        colors = {
            'in': 'green',
            'out': 'red'
        }
        color = colors.get(obj.punch_type, 'black')
        icon = '📥' if obj.punch_type == 'in' else '📤'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_punch_type_display()
        )
    punch_type_display.short_description = "Type"
    
    def status_display(self, obj):
        """Affiche le statut avec une couleur."""
        colors = {
            'normal': 'green',
            'late': 'orange',
            'early': 'orange',
            'missing_out': 'red',
            'double_punch': 'red',
            'outside_zone': 'red',
            'low_accuracy': 'orange'
        }
        color = colors.get(obj.status, 'black')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = "Statut"
    
    def distance_display(self, obj):
        """Affiche la distance avec une couleur selon la zone."""
        if obj.distance_from_site is None:
            return "N/A"
        
        if obj.distance_from_site <= 200:  # Dans la zone
            color = 'green'
            status = '✓'
        else:
            color = 'red'
            status = '✗'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}m</span>',
            color,
            status,
            int(obj.distance_from_site)
        )
    distance_display.short_description = "Distance"
    
    def accuracy_display(self, obj):
        """Affiche la précision GPS avec une couleur."""
        if obj.accuracy is None:
            return "N/A"
        
        if obj.accuracy <= 50:  # Précision acceptable
            color = 'green'
        elif obj.accuracy <= 100:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}m</span>',
            color,
            int(obj.accuracy)
        )
    accuracy_display.short_description = "Précision"
    
    def get_queryset(self, request):
        """Optimise les requêtes avec select_related."""
        return super().get_queryset(request).select_related(
            'employee__employee_profile'
        )
    
    actions = ['mark_as_normal', 'mark_as_late', 'mark_as_early']
    
    def mark_as_normal(self, request, queryset):
        """Marque les pointages sélectionnés comme normaux."""
        updated = queryset.update(status='normal')
        self.message_user(
            request,
            f'{updated} pointage(s) ont été marqué(s) comme normaux.'
        )
    mark_as_normal.short_description = "Marquer comme normaux"
    
    def mark_as_late(self, request, queryset):
        """Marque les pointages sélectionnés comme en retard."""
        updated = queryset.update(status='late')
        self.message_user(
            request,
            f'{updated} pointage(s) ont été marqué(s) comme en retard.'
        )
    mark_as_late.short_description = "Marquer comme en retard"
    
    def mark_as_early(self, request, queryset):
        """Marque les pointages sélectionnés comme sortie anticipée."""
        updated = queryset.update(status='early')
        self.message_user(
            request,
            f'{updated} pointage(s) ont été marqué(s) comme sortie anticipée.'
        )
    mark_as_early.short_description = "Marquer comme sortie anticipée"


@admin.register(AttendanceAnomaly)
class AttendanceAnomalyAdmin(admin.ModelAdmin):
    """
    Configuration de l'administration pour le modèle AttendanceAnomaly.
    """
    
    list_display = [
        'attendance_link',
        'anomaly_type_display',
        'status_display',
        'description_short',
        'resolved_by_name',
        'resolved_at',
        'created_at'
    ]
    
    list_filter = [
        'anomaly_type',
        'status',
        'created_at',
        'resolved_at',
        'attendance__employee__employee_profile__department'
    ]
    
    search_fields = [
        'attendance__employee__first_name',
        'attendance__employee__last_name',
        'attendance__employee__employee_profile__employee_id',
        'description',
        'justification'
    ]
    
    ordering = ['-created_at']
    
    fieldsets = (
        ('Informations de l\'anomalie', {
            'fields': (
                'attendance',
                'anomaly_type',
                'description',
                'status'
            )
        }),
        ('Résolution', {
            'fields': (
                'justification',
                'resolved_by',
                'resolved_at'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'resolved_at']
    
    def attendance_link(self, obj):
        """Affiche un lien vers le pointage concerné."""
        url = reverse('admin:attendance_attendance_change', args=[obj.attendance.pk])
        return format_html(
            '<a href="{}" target="_blank">{} - {}</a>',
            url,
            obj.attendance.employee.get_full_name() or obj.attendance.employee.username,
            obj.attendance.date
        )
    attendance_link.short_description = "Pointage"
    
    def anomaly_type_display(self, obj):
        """Affiche le type d'anomalie avec une couleur."""
        colors = {
            'late_arrival': 'orange',
            'early_departure': 'orange',
            'missing_punch_out': 'red',
            'outside_zone': 'red',
            'low_accuracy': 'orange',
            'double_punch': 'red',
            'long_duration': 'blue'
        }
        color = colors.get(obj.anomaly_type, 'black')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_anomaly_type_display()
        )
    anomaly_type_display.short_description = "Type d'anomalie"
    
    def status_display(self, obj):
        """Affiche le statut avec une couleur."""
        colors = {
            'pending': 'orange',
            'justified': 'blue',
            'resolved': 'green',
            'ignored': 'gray'
        }
        color = colors.get(obj.status, 'black')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = "Statut"
    
    def description_short(self, obj):
        """Affiche une version courte de la description."""
        if len(obj.description) > 50:
            return obj.description[:50] + "..."
        return obj.description
    description_short.short_description = "Description"
    
    def resolved_by_name(self, obj):
        """Affiche le nom de la personne qui a résolu l'anomalie."""
        if obj.resolved_by:
            return obj.resolved_by.get_full_name() or obj.resolved_by.username
        return "Non résolu"
    resolved_by_name.short_description = "Résolu par"
    
    def get_queryset(self, request):
        """Optimise les requêtes avec select_related."""
        return super().get_queryset(request).select_related(
            'attendance__employee__employee_profile',
            'resolved_by'
        )
    
    actions = ['mark_as_resolved', 'mark_as_justified', 'mark_as_ignored']
    
    def mark_as_resolved(self, request, queryset):
        """Marque les anomalies sélectionnées comme résolues."""
        from django.utils import timezone
        updated = queryset.update(
            status='resolved',
            resolved_by=request.user,
            resolved_at=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} anomalie(s) ont été marquée(s) comme résolues.'
        )
    mark_as_resolved.short_description = "Marquer comme résolues"
    
    def mark_as_justified(self, request, queryset):
        """Marque les anomalies sélectionnées comme justifiées."""
        updated = queryset.update(status='justified')
        self.message_user(
            request,
            f'{updated} anomalie(s) ont été marquée(s) comme justifiées.'
        )
    mark_as_justified.short_description = "Marquer comme justifiées"
    
    def mark_as_ignored(self, request, queryset):
        """Marque les anomalies sélectionnées comme ignorées."""
        updated = queryset.update(status='ignored')
        self.message_user(
            request,
            f'{updated} anomalie(s) ont été marquée(s) comme ignorées.'
        )
    mark_as_ignored.short_description = "Marquer comme ignorées"