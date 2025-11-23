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
    
    Formulaire simplifié similaire à l'interface RH.
    IMPORTANT: Limitation à un seul compte RH.
    """
    model = EmployeeProfile
    fk_name = 'user'  # Spécifier la clé étrangère à utiliser
    can_delete = False
    verbose_name_plural = "Profil Employé"
    extra = 1
    max_num = 1
    
    fieldsets = (
        ('Informations employé', {
            'fields': (
                'employee_id',
                'role',
                'department',
                'manager',
                'current_work_schedule'
            ),
            'description': '⚠️ ATTENTION: Un seul compte RH est autorisé dans le système. '
                          'Si vous créez un nouveau compte RH, le précédent sera automatiquement désactivé. '
                          'L\'ID employé sera généré automatiquement si non renseigné.\n\n'
                          '📌 Note: Le RH peut avoir un département (ex: "Ressources Humaines") pour l\'organisation, '
                          'mais ne doit PAS avoir de profil horaire (ne pointe pas) ni de manager (évite les références circulaires). '
                          'Les managers n\'ont pas de manager.'
        }),
    )
    
    def get_formset(self, request, obj=None, **kwargs):
        """Surcharge pour adapter les champs selon le rôle et ajouter la validation RH."""
        formset = super().get_formset(request, obj, **kwargs)
        
        # Rendre tous les champs optionnels (ils seront nettoyés selon le rôle dans save)
        for form in formset.forms:
            if 'department' in form.fields:
                form.fields['department'].required = False
            if 'manager' in form.fields:
                form.fields['manager'].required = False
            if 'current_work_schedule' in form.fields:
                form.fields['current_work_schedule'].required = False
        
        # Vérifier si on essaie de créer un nouveau User avec rôle RH
        original_save = formset.save
        
        def custom_save(commit=True):
            from .user_services import UserService
            
            instances = original_save(commit=False)
            
            for instance in instances:
                if not instance:
                    continue
                
                # Vérifier si c'est une création (pas de pk) ou une modification
                is_new = instance.pk is None
                
                # Générer automatiquement l'ID employé si non renseigné
                if not instance.employee_id:
                    instance.employee_id = UserService.generate_employee_id(instance.role)
                
                # Adapter les valeurs selon le rôle
                if instance.role == 'rh':
                    # RH : peut avoir un département (pour l'organisation, ex: "Ressources Humaines")
                    # MAIS ne doit PAS avoir de profil horaire (ne pointe pas, ne fait pas de demandes)
                    # ET ne doit JAMAIS avoir de manager (évite les références circulaires)
                    if instance.manager is not None:
                        # Forcer manager = None pour éviter les références circulaires
                        instance.manager = None
                    if instance.current_work_schedule is not None:
                        # Pas de profil horaire car le RH ne pointe pas
                        instance.current_work_schedule = None
                    # can_punch doit être False (RH ne pointe pas)
                    if instance.can_punch is not False:
                        instance.can_punch = False
                    
                    # Vérifier s'il existe déjà un RH actif (uniquement lors de la création)
                    if is_new:
                        existing_rh = EmployeeProfile.objects.filter(
                            role='rh',
                            is_active=True
                        ).exists()
                        
                        if existing_rh:
                            from django.contrib import messages
                            messages.error(
                                request,
                                "❌ Impossible de créer un nouveau compte RH. "
                                "Un compte RH existe déjà dans le système. "
                                "Vous devez d'abord désactiver le compte RH existant."
                            )
                            # Ne pas sauvegarder cette instance
                            continue
                
                elif instance.role == 'manager':
                    # Manager : pas de manager (toujours appliquer)
                    instance.manager = None
                    # can_punch peut être modifié manuellement pour un manager
                    if is_new and not hasattr(instance, 'can_punch'):
                        instance.can_punch = True
                
                # Définir les valeurs par défaut uniquement lors de la création
                if is_new:
                    if not hasattr(instance, 'is_active') or instance.is_active is None:
                        instance.is_active = True
                    if not hasattr(instance, 'can_punch') or instance.can_punch is None:
                        # Par défaut, seuls les employés peuvent pointer
                        instance.can_punch = (instance.role == 'employee')
                    if not hasattr(instance, 'employee_type') or not instance.employee_type:
                        instance.employee_type = 'monthly'
            
            if commit:
                return original_save(commit=True)
            return instances
        
        formset.save = custom_save
        
        return formset


# Étendre l'admin User existant
class UserAdmin(BaseUserAdmin):
    """
    Configuration étendue de l'administration pour le modèle User.
    
    Formulaire simplifié similaire à l'interface RH.
    """
    inlines = (EmployeeProfileInline,)
    
    list_display = BaseUserAdmin.list_display + ('employee_profile_display',)
    
    # Simplifier les fieldsets pour ne garder que l'essentiel
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email'),
            'description': '📝 Le username sera généré automatiquement à partir de l\'email. '
                          '🔑 Le mot de passe sera généré automatiquement et envoyé par email. '
                          '👤 Remplissez le formulaire "Profil Employé" ci-dessous pour compléter la création.'
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Surcharge pour masquer le champ username dans le formulaire d'ajout."""
        form = super().get_form(request, obj, **kwargs)
        
        # Si c'est une création (pas une modification), masquer le username
        if not obj:
            if 'username' in form.base_fields:
                form.base_fields['username'].widget = form.base_fields['username'].hidden_widget()
                form.base_fields['username'].required = False
        
        return form
    
    def employee_profile_display(self, obj):
        """Affiche les informations du profil employé."""
        try:
            profile = obj.employee_profile
            role_colors = {
                'employee': 'blue',
                'manager': 'orange', 
                'rh': 'red',
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
    
    def delete_model(self, request, obj):
        """
        Surcharge pour protéger la suppression d'utilisateurs avec des données liées.
        Même logique que l'interface RH pour la cohérence.
        """
        from django.contrib import messages
        from attendance.models import Attendance
        from leave.models import LeaveRequest
        
        # Vérifier si l'utilisateur a un profil employé
        try:
            profile = obj.employee_profile
        except EmployeeProfile.DoesNotExist:
            # Pas de profil employé, suppression autorisée (compte technique)
            super().delete_model(request, obj)
            messages.success(request, f'Utilisateur "{obj.username}" supprimé avec succès.')
            return
        
        # Vérifier les données liées
        has_attendance = Attendance.objects.filter(employee=obj).exists()
        has_leave_requests = LeaveRequest.objects.filter(employee=obj).exists()
        
        related_sources = []
        if has_attendance:
            related_sources.append('pointages')
        if has_leave_requests:
            related_sources.append('demandes de congés')
        
        # Si des données existent, bloquer la suppression
        if related_sources:
            related = ', '.join(related_sources)
            messages.error(
                request,
                f'❌ Impossible de supprimer "{profile.get_full_name()}" car des données existent déjà ({related}). '
                'Désactivez l\'utilisateur à la place (is_active = False).'
            )
            return
        
        # Protection spéciale pour le RH
        if profile.role == 'rh':
            messages.error(
                request,
                '❌ Impossible de supprimer le compte RH. '
                'Désactivez le compte à la place (is_active = False) pour préserver l\'accès au système.'
            )
            return
        
        # Aucune donnée liée, suppression autorisée
        username = obj.username
        super().delete_model(request, obj)
        messages.success(request, f'Utilisateur "{username}" supprimé avec succès.')
    
    def save_model(self, request, obj, form, change):
        """
        Surcharge pour générer automatiquement un mot de passe temporaire,
        un username à partir de l'email, et envoyer un email lors de la création d'un compte avec profil employé.
        """
        from .user_services import UserService
        from django.contrib import messages
        
        # Si c'est une création (pas une modification)
        if not change:
            # Générer automatiquement le username à partir de l'email si non renseigné
            if not obj.username and obj.email:
                obj.username = UserService.generate_username_from_email(obj.email)
            
            # Vérifier si un mot de passe a été défini manuellement
            # Si le mot de passe est vide ou n'a pas été changé, on génère un temporaire
            password_was_set = form.cleaned_data.get('password1') or form.cleaned_data.get('password')
            
            if not password_was_set:
                # Générer un mot de passe temporaire
                temporary_password = UserService.generate_random_password()
                obj.set_password(temporary_password)
                # Stocker le mot de passe temporaire pour l'envoyer par email après la sauvegarde
                obj._temporary_password = temporary_password
            else:
                obj._temporary_password = None
        
        # Sauvegarder le User
        super().save_model(request, obj, form, change)
        
        # Après la sauvegarde, si un profil employé existe, activer force_password_change et envoyer l'email
        if not change:
            try:
                profile = obj.employee_profile
                if profile and profile.employee_id:
                    # Activer le flag force_password_change pour forcer le changement à la première connexion
                    if not profile.force_password_change:
                        profile.force_password_change = True
                        profile.save(update_fields=['force_password_change'])
                    
                    # Si un mot de passe temporaire a été généré, envoyer l'email
                    if hasattr(obj, '_temporary_password') and obj._temporary_password:
                        email_sent = UserService.send_welcome_email(
                            obj, 
                            profile.employee_id, 
                            obj._temporary_password
                        )
                        
                        if email_sent:
                            messages.success(
                                request,
                                f'✓ Compte créé avec succès ! '
                                f'Un email avec les identifiants a été envoyé à {obj.email}. '
                                f'L\'utilisateur devra changer son mot de passe à la première connexion.'
                            )
                        else:
                            messages.warning(
                                request,
                                f'✓ Compte créé avec succès ! '
                                f'ID: {profile.employee_id} | Mot de passe: {obj._temporary_password} '
                                f'(Email non envoyé - communiquez ces informations manuellement)'
                            )
            except EmployeeProfile.DoesNotExist:
                pass  # Pas de profil employé, pas d'email à envoyer


# Réenregistrer User avec notre configuration étendue
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    """
    Configuration de l'administration pour le modèle EmployeeProfile.
    
    IMPORTANT: Limitation à un seul compte RH.
    """
    
    list_display = [
        'employee_id',
        'user_name',
        'role',
        'department',
        'employee_type',
        'can_punch_display',
        'hire_date'
    ]
    
    list_filter = [
        'role',
        'employee_type',
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
    
    def save_model(self, request, obj, form, change):
        """
        Surcharge pour empêcher la création de plusieurs comptes RH.
        """
        # Vérification si on essaie de créer/modifier un compte RH
        if obj.role == 'rh':
            # Si c'est une création (pas une modification)
            if not change:
                # Vérifier s'il existe déjà un compte RH actif
                existing_rh = EmployeeProfile.objects.filter(
                    role='rh',
                    is_active=True
                ).exclude(pk=obj.pk if obj.pk else None).exists()
                
                if existing_rh:
                    from django.contrib import messages
                    messages.error(
                        request,
                        "❌ Impossible de créer un nouveau compte RH. "
                        "Un compte RH existe déjà dans le système. "
                        "Pour créer un nouveau compte RH, vous devez d'abord désactiver ou supprimer le compte RH existant."
                    )
                    return  # Empêcher la sauvegarde
            
            # Si c'est une modification, vérifier qu'on ne désactive pas le dernier RH
            # (permet de modifier le compte RH existant)
        
        super().save_model(request, obj, form, change)
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user', 'employee_id')
        }),
        ('Rôle et département', {
            'fields': ('role', 'department', 'manager')
        }),
        ('Type et statut', {
            'fields': ('employee_type',)
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
