"""
Configuration de l'interface d'administration Django pour l'application leave.

Ce module configure l'interface d'administration pour :
- LeaveType : Gestion des types de congés
- LeaveRequest : Gestion des demandes de congés
- LeaveBalance : Gestion des soldes de congés
- Holiday : Gestion des jours fériés

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from .models import LeaveType, LeaveRequest, LeaveBalance, Holiday


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le modèle LeaveType."""
    
    list_display = [
        'name', 'code', 'unit', 'allocation_type', 'allocation_amount',
        'max_consecutive_days', 'is_paid', 'is_active'
    ]
    
    list_filter = [
        'unit', 'allocation_type', 'requires_justification',
        'requires_medical_certificate', 'is_paid', 'is_active'
    ]
    
    search_fields = ['name', 'code', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'code', 'description', 'color', 'is_active')
        }),
        ('Configuration', {
            'fields': ('unit', 'allocation_type', 'allocation_amount', 'max_consecutive_days')
        }),
        ('Règles et contraintes', {
            'fields': ('requires_justification', 'requires_medical_certificate', 'advance_notice_days', 'is_paid')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    actions = ['activate_types', 'deactivate_types']
    
    def activate_types(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} type(s) de congé ont été activé(s).')
    activate_types.short_description = "Activer les types sélectionnés"
    
    def deactivate_types(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} type(s) de congé ont été désactivé(s).')
    deactivate_types.short_description = "Désactiver les types sélectionnés"


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le modèle LeaveRequest."""
    
    list_display = [
        'employee_name', 'leave_type_name', 'start_date', 'end_date',
        'duration_days', 'priority_display', 'status_display', 'created_at'
    ]
    
    list_filter = [
        'leave_type', 'status', 'priority', 'start_date', 'created_at',
        'employee__employee_profile__department'
    ]
    
    search_fields = [
        'employee__first_name', 'employee__last_name',
        'employee__employee_profile__employee_id', 'reason', 'justification'
    ]
    
    ordering = ['-created_at']
    readonly_fields = ['duration_days', 'created_at', 'updated_at']
    
    def employee_name(self, obj):
        try:
            profile = obj.employee.employee_profile
            return f"{obj.employee.get_full_name() or obj.employee.username} ({profile.employee_id})"
        except:
            return obj.employee.get_full_name() or obj.employee.username
    employee_name.short_description = "Employé"
    
    def leave_type_name(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            obj.leave_type.color, obj.leave_type.name
        )
    leave_type_name.short_description = "Type de congé"
    
    def priority_display(self, obj):
        colors = {'low': 'gray', 'normal': 'blue', 'high': 'orange', 'urgent': 'red'}
        color = colors.get(obj.priority, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_display.short_description = "Priorité"
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange', 'approved_manager': 'lightblue', 'approved_rh': 'green',
            'rejected_manager': 'lightcoral', 'rejected_rh': 'red', 'cancelled': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = "Statut"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'employee__employee_profile', 'leave_type', 'manager'
        )


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le modèle LeaveBalance."""
    
    list_display = [
        'employee_name', 'leave_type_name', 'year', 'allocated_balance',
        'taken_balance', 'remaining_balance_display'
    ]
    
    list_filter = ['leave_type', 'year', 'employee__employee_profile__department']
    
    search_fields = [
        'employee__first_name', 'employee__last_name',
        'employee__employee_profile__employee_id'
    ]
    
    ordering = ['employee', 'leave_type', '-year']
    readonly_fields = ['remaining_balance', 'total_balance', 'created_at', 'updated_at']
    
    def employee_name(self, obj):
        try:
            profile = obj.employee.employee_profile
            return f"{obj.employee.get_full_name() or obj.employee.username} ({profile.employee_id})"
        except:
            return obj.employee.get_full_name() or obj.employee.username
    employee_name.short_description = "Employé"
    
    def leave_type_name(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            obj.leave_type.color, obj.leave_type.name
        )
    leave_type_name.short_description = "Type de congé"
    
    def remaining_balance_display(self, obj):
        remaining = obj.remaining_balance
        color = 'green' if remaining > 0 else 'orange' if remaining == 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, remaining
        )
    remaining_balance_display.short_description = "Solde restant"


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    """Configuration de l'administration pour le modèle Holiday."""
    
    list_display = [
        'name', 'date', 'holiday_type_display', 'is_recurring', 'is_active'
    ]
    
    list_filter = ['holiday_type', 'is_recurring', 'is_active', 'date']
    search_fields = ['name', 'description']
    ordering = ['date']
    readonly_fields = ['created_at', 'updated_at']
    
    def holiday_type_display(self, obj):
        colors = {'national': 'red', 'regional': 'blue', 'company': 'green', 'religious': 'purple'}
        color = colors.get(obj.holiday_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_holiday_type_display()
        )
    holiday_type_display.short_description = "Type"
