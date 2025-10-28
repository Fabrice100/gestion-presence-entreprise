"""
Vues pour la gestion des utilisateurs par les RH.

Ce module contient les vues pour :
- Création et gestion des départements
- Création et gestion des managers
- Création et gestion des employés
- Interface RH pour la gestion organisationnelle

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
from .forms import DepartmentForm, EmployeeProfileForm, EmployeeCreateFormSimple
from .user_services import UserService

# Import du mixin centralisé (principe DRY)
from common.mixins import RHRequiredMixin as BaseRHRequiredMixin


# Alias pour la compatibilité
HRRequiredMixin = BaseRHRequiredMixin


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
        
        queryset = EmployeeProfile.objects.select_related('user', 'department', 'manager').exclude(
            role__in=['admin', 'rh']
        )
        
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
    form_class = EmployeeCreateFormSimple
    
    def get_success_url(self):
        return reverse('hr:user_list')
    
    def form_valid(self, form):
        # Préparer les données
        user_data = {
            'email': form.cleaned_data['email'],
            'first_name': form.cleaned_data.get('first_name', ''),
            'last_name': form.cleaned_data.get('last_name', ''),
        }
        
        profile_data = {
            'department': form.cleaned_data.get('department'),
            'manager': None,  # Les managers n'ont pas de manager
            'role': 'manager',
            'current_work_schedule': form.cleaned_data.get('current_work_schedule'),
        }
        
        # Créer le manager avec génération automatique des credentials
        user, employee_id, temporary_password = UserService.create_employee_with_credentials(
            user_data, profile_data
        )
        
        if user:
            # Envoyer l'email de bienvenue
            email_sent = UserService.send_welcome_email(user, employee_id, temporary_password)
            
            if email_sent:
                messages.success(
                    self.request,
                    f'Manager "{user.username}" créé avec succès ! '
                    f'Un email avec les identifiants a été envoyé à {user.email}.'
                )
            else:
                messages.warning(
                    self.request,
                    f'Manager "{user.username}" créé avec succès ! '
                    f'ID: {employee_id} | Mot de passe: {temporary_password} '
                    f'(Email non envoyé - communiquez ces informations manuellement)'
                )
        else:
            messages.error(self.request, 'Erreur lors de la création du manager.')
        
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
    form_class = EmployeeCreateFormSimple
    
    def get_success_url(self):
        return reverse('hr:user_list')
    
    def form_valid(self, form):
        # Préparer les données
        user_data = {
            'email': form.cleaned_data['email'],
            'first_name': form.cleaned_data.get('first_name', ''),
            'last_name': form.cleaned_data.get('last_name', ''),
        }
        
        profile_data = {
            'department': form.cleaned_data.get('department'),
            'manager': form.cleaned_data.get('manager'),
            'role': 'employee',  # ✅ TOUJOURS 'employee' pour RH
            'current_work_schedule': form.cleaned_data.get('current_work_schedule'),
        }
        
        # ✅ SÉCURITÉ : Validation stricte du rôle
        # RH ne peut créer QUE des employés
        if 'role' in form.cleaned_data:
            if form.cleaned_data['role'] not in ['employee']:
                messages.error(self.request, 'Seuls les employés peuvent être créés via cette interface.')
                return self.form_invalid(form)
        
        # Créer l'employé avec génération automatique des credentials
        user, employee_id, temporary_password = UserService.create_employee_with_credentials(
            user_data, profile_data
        )
        
        if user:
            # Envoyer l'email de bienvenue
            email_sent = UserService.send_welcome_email(user, employee_id, temporary_password)
            
            if email_sent:
                messages.success(
                    self.request,
                    f'Employé "{user.username}" créé avec succès ! '
                    f'Un email avec les identifiants a été envoyé à {user.email}.'
                )
            else:
                messages.warning(
                    self.request,
                    f'Employé "{user.username}" créé avec succès ! '
                    f'ID: {employee_id} | Mot de passe: {temporary_password} '
                    f'(Email non envoyé - communiquez ces informations manuellement)'
                )
        else:
            messages.error(self.request, 'Erreur lors de la création de l\'employé.')
        
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
    if not request.user.employee_profile.is_rh():
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


# ============================================================================
# VUES POUR LA GESTION DES PROFILS HORAIRES
# ============================================================================

class WorkScheduleListView(HRRequiredMixin, ListView):
    """
    Liste de tous les profils horaires.
    Interface RH pour gérer les profils.
    """
    model = None  # Sera importé dynamiquement
    template_name = 'hr/schedule_list.html'
    context_object_name = 'schedules'
    paginate_by = 20
    
    def get_model(self):
        from accounts.models import WorkSchedule
        return WorkSchedule
    
    def get_queryset(self):
        from accounts.models import WorkSchedule
        return WorkSchedule.objects.all().order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Gestion des Profils Horaires'
        context['schedules'] = context['object_list']
        
        # Ajouter le nombre d'employés par profil
        for schedule in context['schedules']:
            schedule.employee_count = schedule.get_employee_count()
        
        return context


class WorkScheduleCreateView(HRRequiredMixin, CreateView):
    """
    Création d'un nouveau profil horaire.
    """
    model = None
    form_class = None
    template_name = 'hr/schedule_form.html'
    success_url = reverse_lazy('hr:hr_schedule_list')
    
    def get_model(self):
        from accounts.models import WorkSchedule
        return WorkSchedule
    
    def get_form_class(self):
        from accounts.schedule_forms import WorkScheduleForm
        return WorkScheduleForm
    
    def form_valid(self, form):
        # Enregistrer qui a créé le profil
        form.instance.created_by = self.request.user
        messages.success(self.request, f'✅ Profil horaire "{form.instance.name}" créé avec succès.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Créer un Profil Horaire'
        context['submit_text'] = 'Créer le profil'
        return context


class WorkScheduleUpdateView(HRRequiredMixin, UpdateView):
    """
    Modification d'un profil horaire existant.
    """
    model = None
    form_class = None
    template_name = 'hr/schedule_form.html'
    success_url = reverse_lazy('hr:hr_schedule_list')
    
    def get_model(self):
        from accounts.models import WorkSchedule
        return WorkSchedule
    
    def get_form_class(self):
        from accounts.schedule_forms import WorkScheduleForm
        return WorkScheduleForm
    
    def get_queryset(self):
        from accounts.models import WorkSchedule
        return WorkSchedule.objects.all()
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Profil horaire "{form.instance.name}" modifié avec succès.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Modifier le Profil "{self.object.name}"'
        context['submit_text'] = 'Enregistrer les modifications'
        return context


class WorkScheduleDetailView(HRRequiredMixin, TemplateView):
    """
    Détails d'un profil horaire avec liste des employés affectés.
    """
    template_name = 'hr/schedule_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from accounts.models import WorkSchedule
        schedule = get_object_or_404(WorkSchedule, pk=kwargs['pk'])
        
        # Employés actuellement sur ce profil
        from accounts.schedule_service import WorkScheduleService
        employees = WorkScheduleService.get_employees_by_schedule(schedule, active_only=True)
        
        context.update({
            'schedule': schedule,
            'employees': employees,
            'employee_count': employees.count(),
            'page_title': f'Profil "{schedule.name}"'
        })
        
        return context


class WorkScheduleDeleteView(HRRequiredMixin, DeleteView):
    """
    Suppression d'un profil horaire (avec vérifications).
    """
    model = None
    template_name = 'hr/schedule_confirm_delete.html'
    success_url = reverse_lazy('hr:hr_schedule_list')
    
    def get_model(self):
        from accounts.models import WorkSchedule
        return WorkSchedule
    
    def get_queryset(self):
        from accounts.models import WorkSchedule
        return WorkSchedule.objects.all()
    
    def delete(self, request, *args, **kwargs):
        from accounts.schedule_service import WorkScheduleService
        
        self.object = self.get_object()
        
        # Vérifier si le profil peut être supprimé
        can_delete, reason = WorkScheduleService.can_delete_schedule(self.object)
        
        if not can_delete:
            messages.error(request, f'❌ Impossible de supprimer ce profil : {reason}')
            return redirect('accounts:hr_schedule_detail', pk=self.object.pk)
        
        schedule_name = self.object.name
        messages.success(request, f'✅ Profil horaire "{schedule_name}" supprimé avec succès.')
        return super().delete(request, *args, **kwargs)


@login_required
def change_employee_schedule_view(request, employee_id):
    """
    Vue pour changer le profil horaire d'un employé.
    """
    # Vérifier que l'utilisateur est RH
    if not hasattr(request.user, 'employee_profile') or request.user.employee_profile.role != 'rh':
        messages.error(request, '❌ Accès refusé. Réservé aux RH.')
        return redirect('dashboard:dashboard')
    
    employee = get_object_or_404(EmployeeProfile, pk=employee_id)
    
    if request.method == 'POST':
        from accounts.schedule_forms import ChangeEmployeeScheduleForm
        form = ChangeEmployeeScheduleForm(request.POST)
        
        if form.is_valid():
            from accounts.schedule_service import WorkScheduleService
            
            new_schedule = form.cleaned_data['new_schedule']
            
            # Changer le profil avec historisation
            WorkScheduleService.change_employee_schedule(
                employee=employee,
                new_schedule=new_schedule,
                assigned_by_user=request.user
            )
            
            messages.success(
                request,
                f'✅ Profil horaire de {employee.user.get_full_name()} changé vers "{new_schedule.name}"'
            )
            
            return redirect('accounts:hr_employee_detail', pk=employee_id)
    else:
        from accounts.schedule_forms import ChangeEmployeeScheduleForm
        form = ChangeEmployeeScheduleForm()
    
    context = {
        'employee': employee,
        'form': form,
        'page_title': f'Changer le profil horaire de {employee.user.get_full_name()}'
    }
    
    return render(request, 'hr/change_employee_schedule.html', context)
