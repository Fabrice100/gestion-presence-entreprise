"""
Vues pour la configuration du système de pointage.

Accessible uniquement par les administrateurs et RH/DG.
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
    
    ADMIN : Configuration complète (technique + métier)
    RH/DG : Configuration métier uniquement (horaires)
    """
    model = CompanySettings
    template_name = 'attendance/company_settings.html'
    success_url = reverse_lazy('attendance:company_settings')
    
    def get_form_fields(self):
        """Retourne les champs selon le rôle."""
        try:
            profile = self.request.user.employee_profile
            role = profile.role
        except:
            # Superuser = admin
            role = 'admin' if self.request.user.is_superuser else None
        
        if role == 'admin':
            # ADMIN : Tous les champs (technique + métier)
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
        elif role == 'rh_dg':
            # RH/DG : Uniquement champs métier
            return [
                'work_start_time',
                'work_end_time',
                'late_tolerance_minutes',
            ]
        else:
            return []
    
    @property
    def fields(self):
        """Champs dynamiques selon le rôle."""
        return self.get_form_fields()
    
    def dispatch(self, request, *args, **kwargs):
        """Vérifier les permissions."""
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        # Seuls Admin et RH/DG peuvent accéder
        try:
            profile = request.user.employee_profile
            if profile.role not in ['admin', 'rh_dg']:
                messages.error(request, 'Accès refusé. Réservé aux administrateurs et RH.')
                return redirect('dashboard:dashboard')
        except:
            if not request.user.is_superuser:
                messages.error(request, 'Accès refusé.')
                return redirect('dashboard:dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
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
            role = 'admin' if self.request.user.is_superuser else None
        
        context.update({
            'page_title': 'Configuration Système',
            'settings': settings,
            'user_role': role,
            'is_admin': role == 'admin',
            'is_rh': role == 'rh_dg',
        })
        
        return context

