"""
Vues pour la gestion des utilisateurs par les RH/DG.

Ce module contient les vues pour :
- Création et gestion des départements
- Création et gestion des managers
- Création et gestion des employés
- Interface RH/DG pour la gestion organisationnelle

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
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password

from .models import EmployeeProfile, Department
from .forms import DepartmentForm, UserCreateForm, EmployeeProfileForm


class HRRequiredMixin:
    """Mixin pour exiger le rôle RH/DG."""
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not hasattr(self.request.user, 'employee_profile'):
            messages.error(self.request, 'Profil employé non trouvé.')
            return redirect('dashboard:dashboard')
        
        if not self.request.user.employee_profile.is_rh_dg():
            messages.error(self.request, 'Accès refusé. Seuls les RH/DG peuvent accéder à cette fonctionnalité.')
            return redirect('dashboard:dashboard')
        
        return super().dispatch(*args, **kwargs)


class HRDashboardView(HRRequiredMixin, TemplateView):
    """
    Tableau de bord RH/DG avec gestion des utilisateurs.
    """
    template_name = 'hr/hr_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Statistiques générales
        context.update({
            'total_departments': Department.objects.count(),
            'total_managers': EmployeeProfile.objects.filter(role='manager').count(),
            'total_employees': EmployeeProfile.objects.filter(role='employee').count(),
            'total_users': User.objects.count(),
            'active_departments': Department.objects.filter(is_active=True).count(),
            'active_employees': EmployeeProfile.objects.filter(is_active=True).count(),
        })
        
        # Départements récents
        context['recent_departments'] = Department.objects.all().order_by('-created_at')[:5]
        
        # Utilisateurs récents
        context['recent_users'] = EmployeeProfile.objects.all().order_by('-created_at')[:5]
        
        return context


class DepartmentListView(HRRequiredMixin, ListView):
    """
    Liste des départements.
    """
    model = Department
    template_name = 'hr/department_list.html'
    context_object_name = 'departments'
    paginate_by = 20
    
    def get_queryset(self):
        return Department.objects.all().order_by('name')


class DepartmentCreateView(HRRequiredMixin, CreateView):
    """
    Création d'un département.
    """
    model = Department
    form_class = DepartmentForm
    template_name = 'hr/department_form.html'
    success_url = reverse_lazy('hr:department_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Département "{form.instance.name}" créé avec succès.')
        return super().form_valid(form)


class DepartmentUpdateView(HRRequiredMixin, UpdateView):
    """
    Modification d'un département.
    """
    model = Department
    form_class = DepartmentForm
    template_name = 'hr/department_form.html'
    success_url = reverse_lazy('hr:department_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Département "{form.instance.name}" modifié avec succès.')
        return super().form_valid(form)


class DepartmentDeleteView(HRRequiredMixin, DeleteView):
    """
    Suppression d'un département.
    """
    model = Department
    template_name = 'hr/department_confirm_delete.html'
    success_url = reverse_lazy('hr:department_list')
    
    def delete(self, request, *args, **kwargs):
        department = self.get_object()
        messages.success(request, f'Département "{department.name}" supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


class UserListView(HRRequiredMixin, ListView):
    """
    Liste des utilisateurs.
    """
    model = EmployeeProfile
    template_name = 'hr/user_list.html'
    context_object_name = 'profiles'
    paginate_by = 20
    
    def get_queryset(self):
        role = self.request.GET.get('role')
        department_id = self.request.GET.get('department')
        
        queryset = EmployeeProfile.objects.select_related('user', 'department', 'manager')
        
        if role:
            queryset = queryset.filter(role=role)
        
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        return queryset.order_by('employee_id')


class ManagerCreateView(HRRequiredMixin, CreateView):
    """
    Création d'un manager.
    """
    template_name = 'hr/manager_form.html'
    form_class = UserCreateForm
    
    def get_success_url(self):
        return reverse('hr:user_list')
    
    def form_valid(self, form):
        # Créer l'utilisateur
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        
        # Créer le profil employé
        profile = EmployeeProfile.objects.create(
            user=user,
            employee_id=f"MGR{EmployeeProfile.objects.filter(role='manager').count() + 1:03d}",
            role='manager',
            department=form.cleaned_data['department'],
            phone=form.cleaned_data.get('phone', ''),
            is_active=True,
            can_punch=True,  # Les managers pointent
        )
        
        messages.success(self.request, f'Manager "{user.username}" créé avec succès.')
        return redirect(self.get_success_url())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].fields['department'].queryset = Department.objects.filter(is_active=True)
        return context


class EmployeeCreateView(HRRequiredMixin, CreateView):
    """
    Création d'un employé.
    """
    template_name = 'hr/employee_form.html'
    form_class = UserCreateForm
    
    def get_success_url(self):
        return reverse('hr:user_list')
    
    def form_valid(self, form):
        # Créer l'utilisateur
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        
        # Créer le profil employé
        profile = EmployeeProfile.objects.create(
            user=user,
            employee_id=f"EMP{EmployeeProfile.objects.filter(role='employee').count() + 1:03d}",
            role='employee',
            department=form.cleaned_data['department'],
            manager=form.cleaned_data.get('manager'),
            phone=form.cleaned_data.get('phone', ''),
            is_active=True,
            can_punch=True,  # Les employés pointent
        )
        
        messages.success(self.request, f'Employé "{user.username}" créé avec succès.')
        return redirect(self.get_success_url())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].fields['department'].queryset = Department.objects.filter(is_active=True)
        context['form'].fields['manager'].queryset = User.objects.filter(
            employee_profile__role='manager',
            employee_profile__is_active=True
        )
        return context


class UserUpdateView(HRRequiredMixin, UpdateView):
    """
    Modification d'un utilisateur.
    """
    model = EmployeeProfile
    form_class = EmployeeProfileForm
    template_name = 'hr/user_form.html'
    success_url = reverse_lazy('hr:user_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Utilisateur "{form.instance.user.username}" modifié avec succès.')
        return super().form_valid(form)


class UserDeleteView(HRRequiredMixin, DeleteView):
    """
    Suppression d'un utilisateur.
    """
    model = EmployeeProfile
    template_name = 'hr/user_confirm_delete.html'
    success_url = reverse_lazy('hr:user_list')
    
    def delete(self, request, *args, **kwargs):
        profile = self.get_object()
        username = profile.user.username
        messages.success(request, f'Utilisateur "{username}" supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


def get_managers_by_department(request):
    """
    API pour récupérer les managers d'un département.
    """
    if not request.user.employee_profile.is_rh_dg():
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    
    department_id = request.GET.get('department_id')
    if department_id:
        managers = User.objects.filter(
            employee_profile__department_id=department_id,
            employee_profile__role='manager',
            employee_profile__is_active=True
        ).values('id', 'username', 'first_name', 'last_name')
        
        return JsonResponse({'managers': list(managers)})
    
    return JsonResponse({'managers': []})
