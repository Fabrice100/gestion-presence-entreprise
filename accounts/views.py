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
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q

from .models import EmployeeProfile, Department


class LoginRequiredMixin:
    """Mixin pour exiger une authentification."""
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Vue pour afficher le profil de l'utilisateur connecté.
    """
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.request.user.employee_profile
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """
    Vue pour modifier le profil de l'utilisateur connecté.
    """
    model = EmployeeProfile
    template_name = 'accounts/profile_edit.html'
    fields = ['phone', 'address']
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        """Retourne le profil de l'utilisateur connecté."""
        return self.request.user.employee_profile
    
    def form_valid(self, form):
        """Sauvegarde le formulaire et affiche un message de succès."""
        messages.success(self.request, 'Votre profil a été mis à jour avec succès.')
        return super().form_valid(form)


class UserListView(LoginRequiredMixin, ListView):
    """
    Vue pour lister tous les utilisateurs (admin seulement).
    """
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtre les utilisateurs selon les permissions."""
        if not self.request.user.employee_profile.is_admin():
            return User.objects.none()
        
        queryset = User.objects.select_related('employee_profile').order_by('employee_profile__employee_id')
        
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


class UserDetailView(LoginRequiredMixin, DetailView):
    """
    Vue pour afficher les détails d'un utilisateur.
    """
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_detail'
    
    def get_queryset(self):
        """Filtre selon les permissions."""
        if not self.request.user.employee_profile.is_admin():
            return User.objects.none()
        return User.objects.select_related('employee_profile')


class UserEditView(LoginRequiredMixin, UpdateView):
    """
    Vue pour modifier un utilisateur (admin seulement).
    """
    model = EmployeeProfile
    template_name = 'accounts/user_edit.html'
    fields = ['role', 'department', 'manager', 'employee_type', 'status', 'can_punch']
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


class DepartmentDetailView(LoginRequiredMixin, DetailView):
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