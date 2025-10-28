"""
Vues pour l'application accounts (authentification et gestion des comptes).

Ce module contient les vues pour :
- Authentification (login, logout, password)
- Gestion des profils utilisateurs
- Inscription et activation des comptes

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView as DjangoPasswordChangeView
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django_ratelimit.decorators import ratelimit

# Import du mixin centralisé (principe DRY)
from common.mixins import (
    EnhancedLoginRequiredMixin, 
    AdminRequiredMixin,
    EmployeeRequiredMixin
)

from .models import EmployeeProfile, Department


@require_http_methods(["GET", "POST"])
@csrf_exempt
def simple_logout(request):
    """
    Fonction de déconnexion simple qui accepte GET et POST.
    """
    if request.user.is_authenticated:
        logout(request)
    return redirect('/accounts/login/')


@method_decorator(csrf_exempt, name='dispatch')
class CustomLogoutView(View):
    """
    Vue de déconnexion personnalisée qui accepte GET et POST.
    """
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
        return HttpResponseRedirect('/accounts/login/')
    
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
        return HttpResponseRedirect('/accounts/login/')


class CustomLoginView(LoginView):
    """
    Vue de connexion personnalisée avec protection rate limiting.
    
    Utilise le backend d'authentification personnalisé pour permettre
    la connexion avec l'ID Employé.
    Protégée contre les attaques par force brute.
    """
    template_name = 'accounts/login_ultra_modern.html'
    redirect_authenticated_user = True  # Rediriger si déjà authentifié
    
    @method_decorator(ratelimit(key='ip', rate=settings.RATELIMIT_LOGIN_RATE, method='POST', block=True))
    def post(self, request, *args, **kwargs):
        """POST avec protection rate limiting."""
        return super().post(request, *args, **kwargs)
    
    def get_success_url(self):
        """Redirige vers le tableau de bord après connexion."""
        return reverse_lazy('dashboard:dashboard')
    
    def form_valid(self, form):
        """Traite la connexion réussie."""
        response = super().form_valid(form)
        # Message de bienvenue désactivé pour éviter l'alerte verte à chaque connexion
        return response


class ProfileView(EnhancedLoginRequiredMixin, TemplateView):
    """
    Vue pour afficher le profil de l'utilisateur connecté.
    """
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.request.user.employee_profile
        return context


class ProfileEditView(EnhancedLoginRequiredMixin, UpdateView):
    """
    Vue pour modifier le profil de l'utilisateur connecté.
    """
    model = EmployeeProfile
    template_name = 'accounts/profile_edit.html'
    fields = ['phone']
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        """Retourne le profil de l'utilisateur connecté."""
        return self.request.user.employee_profile
    
    def form_valid(self, form):
        """Sauvegarde le formulaire et affiche un message de succès."""
        messages.success(self.request, 'Votre profil a été mis à jour avec succès.')
        return super().form_valid(form)


class UserListView(AdminRequiredMixin, ListView):
    """
    Vue pour lister tous les utilisateurs (admin seulement).
    """
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtre les utilisateurs selon les permissions."""
        # Vérifier permissions RH
        if not self.request.user.employee_profile.is_rh():
            return User.objects.none()
        
        queryset = User.objects.select_related('employee_profile').exclude(
            employee_profile__role='rh'
        ).order_by('employee_profile__employee_id')
        
        # Filtres
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search) |
                Q(employee_profile__employee_id__icontains=search)
            )
        
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(employee_profile__department_id=department)
        
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(employee_profile__role=role)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.filter(is_active=True)
        context['roles'] = EmployeeProfile.ROLE_CHOICES
        return context


class UserDetailView(AdminRequiredMixin, DetailView):
    """
    Vue pour afficher les détails d'un utilisateur.
    """
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_detail'
    
    def get_queryset(self):
        """Filtre selon les permissions."""
        return User.objects.select_related('employee_profile').exclude(
            employee_profile__role='rh'
        )


class UserEditView(AdminRequiredMixin, UpdateView):
    """
    Vue pour modifier un utilisateur (admin seulement).
    """
    model = EmployeeProfile
    template_name = 'accounts/user_edit.html'
    fields = ['role', 'department', 'manager', 'employee_type', 'can_punch']
    success_url = reverse_lazy('accounts:user_list')
    
    def get_object(self):
        """Retourne le profil de l'utilisateur à modifier."""
        user = get_object_or_404(User, pk=self.kwargs['pk'])
        return user.employee_profile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.filter(is_active=True)
        context['managers'] = User.objects.filter(
            employee_profile__role='manager',
            employee_profile__is_active=True
        )
        return context
    
    def form_valid(self, form):
        """Sauvegarde le formulaire et affiche un message de succès."""
        messages.success(self.request, f'Le profil de {self.object.user.get_full_name()} a été mis à jour.')
        return super().form_valid(form)


class DepartmentListView(LoginRequiredMixin, ListView):
    """
    Vue pour lister tous les départements.
    """
    model = Department
    template_name = 'accounts/department_list.html'
    context_object_name = 'departments'
    
    def get_queryset(self):
        """Filtre les départements actifs."""
        return Department.objects.filter(is_active=True).prefetch_related('employees')


class DepartmentDetailView(EnhancedLoginRequiredMixin, DetailView):
    """
    Vue pour afficher les détails d'un département.
    """
    model = Department
    template_name = 'accounts/department_detail.html'
    context_object_name = 'department'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employees'] = self.object.employees.filter(is_active=True).select_related('user')
        return context


class CustomPasswordChangeView(DjangoPasswordChangeView):
    """
    Vue personnalisée pour le changement de mot de passe.
    Désactive le flag force_password_change après un changement réussi.
    """
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')
    
    def form_valid(self, form):
        """
        Désactive le flag force_password_change après un changement réussi.
        """
        response = super().form_valid(form)
        
        # Désactiver le flag si l'utilisateur a un profil
        if hasattr(self.request.user, 'employee_profile'):
            profile = self.request.user.employee_profile
            if profile.force_password_change:
                profile.force_password_change = False
                profile.save()
                messages.success(
                    self.request,
                    'Mot de passe changé avec succès ! Vous pouvez maintenant accéder au système.'
                )
        
        return response