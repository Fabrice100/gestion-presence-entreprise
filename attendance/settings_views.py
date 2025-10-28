"""
Vues pour la configuration du système de pointage.

ACCÈS RÉSERVÉ AUX ADMINISTRATEURS SYSTÈME UNIQUEMENT

Les RH n'ont pas accès à cette configuration pour des raisons de sécurité.
La configuration système (GPS, horaires) doit être gérée par l'administrateur technique.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .admin_models import CompanySettings


class CompanySettingsView(LoginRequiredMixin, UpdateView):
    """
    Vue pour modifier la configuration de l'entreprise.
    
    RÉSERVÉ AUX ADMINISTRATEURS UNIQUEMENT
    
    Configuration technique et système :
    - Paramètres GPS (géolocalisation, rayon autorisé)
    - Horaires de travail de l'entreprise
    - Tolérance de retard
    
    Politique de sécurité :
    - Seuls les superusers (admins Django) ont accès
    - Les RH gèrent le personnel, pas les paramètres système
    """
    model = CompanySettings
    template_name = 'attendance/company_settings.html'
    success_url = reverse_lazy('attendance:company_settings')
    
    def get_form_fields(self):
        """
        Retourne les champs de configuration.
        
        POLITIQUE DE SÉCURITÉ :
        - Superuser uniquement : Configuration complète
        - Autres rôles : Accès refusé
        """
        # SÉCURITÉ : Seul le superuser peut configurer le système
        if self.request.user.is_superuser:
            # SUPERUSER : Configuration complète (GPS + horaires)
            return [
                'company_name',
                'work_start_time',
                'work_end_time',
                'late_tolerance_minutes',
                'gps_required',
                'site_center_latitude',
                'site_center_longitude',
                'allowed_radius_meters',
                'gps_accuracy_max_meters',
            ]
        
        # Tous les autres utilisateurs : pas d'accès
        return []
    
    @property
    def fields(self):
        """Champs dynamiques selon le rôle."""
        return self.get_form_fields()
    
    def dispatch(self, request, *args, **kwargs):
        """
        Vérifier les permissions d'accès.
        
        Accès autorisé uniquement à :
        - Superuser (admin Django) : accès complet
        
        Tous les autres utilisateurs (y compris RH) :
        - Redirection vers dashboard avec message d'erreur
        """
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Seul le superuser a accès
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        # Tous les autres : accès refusé
        messages.error(request, '⚠️ Accès refusé. Configuration réservée aux administrateurs système.')
        return redirect('dashboard:dashboard')
    
    def get_object(self, queryset=None):
        """Récupère ou crée la configuration unique."""
        return CompanySettings.load()
    
    def form_valid(self, form):
        """Enregistre l'utilisateur qui a modifié."""
        form.instance.updated_by = self.request.user
        messages.success(
            self.request,
            '✅ Configuration mise à jour avec succès !'
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = self.get_object()
        
        # Déterminer le rôle
        try:
            profile = self.request.user.employee_profile
            role = profile.role
        except:
            role = None
        
        context.update({
            'page_title': 'Configuration Système',
            'settings': settings,
            'user_role': role,
            'is_superuser': self.request.user.is_superuser,
            'is_rh': role == 'rh',
        })
        
        return context

