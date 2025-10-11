"""
Configuration de l'interface d'administration Django pour l'application accounts.

Ce module configure l'interface d'administration pour :
- Department : Gestion des départements
- EmployeeProfile : Gestion des profils employés

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Department, EmployeeProfile


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Configuration de l'administration pour le modèle Department.
    """
    
    list_display = [
        'name', 
        'manager_name', 
        'employee_count', 
        'is_active', 
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'name',
        'description',
        'manager__first_name',
        'manager__last_name',
        'manager__username'
    ]
    
    ordering = ['name']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Management', {
            'fields': ('manager',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def manager_name(self, obj):
        """Affiche le nom du manager."""
        if obj.manager:
            return f"{obj.manager.get_full_name() or obj.manager.username}"
        return "Aucun"
    manager_name.short_description = "Manager"
    
    def employee_count(self, obj):
        """Affiche le nombre d'employés dans le département."""
        count = obj.get_employee_count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return format_html(
            '<span style="color: gray;">{}</span>',
            count
        )
    employee_count.short_description = "Nb Employés"


class EmployeeProfileInline(admin.StackedInline):
    """
    Inline admin pour afficher le profil employé dans l'admin User.
    """
    model = EmployeeProfile
    fk_name = 'user'  # Spécifier la clé étrangère à utiliser
    can_delete = False
    verbose_name_plural = "Profil Employé"
    
    fieldsets = (
        ('Informations employé', {
            'fields': (
                'employee_id',
                'role',
                'employee_type',
                'status',
                'department',
                'manager'
            )
        }),
        ('Informations personnelles', {
            'fields': (
                'address',
            )
        }),
        ('Contrat', {
            'fields': (
                'hire_date',
                'contract_end_date'
            )
        }),
        ('Permissions', {
            'fields': (
                'can_punch',
                'is_active'
            )
        }),
    )


# Étendre l'admin User existant
class UserAdmin(BaseUserAdmin):
    """
    Configuration étendue de l'administration pour le modèle User.
    """
    inlines = (EmployeeProfileInline,)
    
    list_display = BaseUserAdmin.list_display + ('employee_profile_display',)
    
    def employee_profile_display(self, obj):
        """Affiche les informations du profil employé."""
        try:
            profile = obj.employee_profile
            role_colors = {
                'employee': 'blue',
                'manager': 'orange', 
                'rh_dg': 'red',
                'admin': 'purple'
            }
            color = role_colors.get(profile.role, 'black')
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span> - {}',
                color,
                profile.get_role_display(),
                profile.employee_id
            )
        except EmployeeProfile.DoesNotExist:
            return format_html(
                '<span style="color: red;">Aucun profil</span>'
            )
    
    employee_profile_display.short_description = "Profil Employé"


# Réenregistrer User avec notre configuration étendue
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    """
    Configuration de l'administration pour le modèle EmployeeProfile.
    """
    
    list_display = [
        'employee_id',
        'user_name',
        'role',
        'department',
        'employee_type',
        'status',
        'can_punch_display',
        'hire_date'
    ]
    
    list_filter = [
        'role',
        'employee_type',
        'status',
        'department',
        'can_punch',
        'is_active',
        'hire_date'
    ]
    
    search_fields = [
        'employee_id',
        'user__first_name',
        'user__last_name',
        'user__username',
        'user__email',
    ]
    
    ordering = ['employee_id']
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user', 'employee_id')
        }),
        ('Rôle et département', {
            'fields': ('role', 'department', 'manager')
        }),
        ('Type et statut', {
            'fields': ('employee_type', 'status')
        }),
        ('Informations personnelles', {
            'fields': ('address',)
        }),
        ('Contrat', {
            'fields': ('hire_date', 'contract_end_date')
        }),
        ('Permissions', {
            'fields': ('can_punch', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['employee_id', 'created_at', 'updated_at']
    
    def user_name(self, obj):
        """Affiche le nom complet de l'utilisateur."""
        return obj.get_full_name()
    user_name.short_description = "Nom complet"
    
    def can_punch_display(self, obj):
        """Affiche si l'employé peut pointer avec un indicateur visuel."""
        if obj.can_punch:
            return format_html(
                '<span style="color: green;">✓ Peut pointer</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Ne peut pas pointer</span>'
        )
    can_punch_display.short_description = "Pointage"
    
    def get_queryset(self, request):
        """Optimise les requêtes avec select_related."""
        return super().get_queryset(request).select_related(
            'user', 'department', 'manager'
        )
    
    actions = ['activate_employees', 'deactivate_employees', 'enable_punching', 'disable_punching']
    
    def activate_employees(self, request, queryset):
        """Active les employés sélectionnés."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} employé(s) ont été activé(s).'
        )
    activate_employees.short_description = "Activer les employés sélectionnés"
    
    def deactivate_employees(self, request, queryset):
        """Désactive les employés sélectionnés."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} employé(s) ont été désactivé(s).'
        )
    deactivate_employees.short_description = "Désactiver les employés sélectionnés"
    
    def enable_punching(self, request, queryset):
        """Active le pointage pour les employés sélectionnés."""
        updated = queryset.update(can_punch=True)
        self.message_user(
            request,
            f'Le pointage a été activé pour {updated} employé(s).'
        )
    enable_punching.short_description = "Activer le pointage"
    
    def disable_punching(self, request, queryset):
        """Désactive le pointage pour les employés sélectionnés."""
        updated = queryset.update(can_punch=False)
        self.message_user(
            request,
            f'Le pointage a été désactivé pour {updated} employé(s).'
        )
    disable_punching.short_description = "Désactiver le pointage"