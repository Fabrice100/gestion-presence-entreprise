"""
Vues pour le workflow de validation des congés.

Ce module contient les vues pour :
- Création de demandes de congés
- Validation par les managers
- Validation finale par RH/DG
- Gestion des soldes de congés
- Notifications et alertes

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
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from django.db import transaction

from .models import LeaveRequest, LeaveType, LeaveBalance
from .forms import LeaveRequestForm, LeaveApprovalForm
from accounts.models import EmployeeProfile


class LeaveRequestListView(LoginRequiredMixin, ListView):
    """
    Liste des demandes de congés pour l'utilisateur connecté.
    """
    model = LeaveRequest
    template_name = 'leave/leave_request_list.html'
    context_object_name = 'leave_requests'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        return LeaveRequest.objects.filter(
            employee=user
        ).select_related('leave_type').order_by('-created_at')


class LeaveRequestCreateView(LoginRequiredMixin, CreateView):
    """
    Création d'une nouvelle demande de congé.
    """
    model = LeaveRequest
    form_class = LeaveRequestForm
    template_name = 'leave/leave_request_create.html'
    success_url = reverse_lazy('leave:leave_request_list')
    
    def form_valid(self, form):
        # Vérifier le solde de congés
        leave_type = form.cleaned_data['leave_type']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        
        # Calculer le nombre de jours demandés
        days_requested = (end_date - start_date).days + 1
        
        # Vérifier le solde disponible
        balance, created = LeaveBalance.objects.get_or_create(
            employee=self.request.user,
            leave_type=leave_type,
            year=start_date.year,
            defaults={'allocated_balance': leave_type.allocation_amount, 'taken_balance': 0}
        )
        
        if balance.remaining_balance < days_requested:
            form.add_error(None, f'Solde insuffisant. Disponible: {balance.remaining_balance} jours, Demandé: {days_requested} jours')
            return self.form_invalid(form)
        
        # Vérifier les chevauchements
        overlapping_requests = LeaveRequest.objects.filter(
            employee=self.request.user,
            status__in=['pending', 'approved'],
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        if overlapping_requests.exists():
            form.add_error(None, 'Vous avez déjà une demande de congé sur cette période')
            return self.form_invalid(form)
        
        # Créer la demande
        leave_request = form.save(commit=False)
        leave_request.employee = self.request.user
        leave_request.status = 'pending'
        
        # Calculer la durée
        days_requested = (end_date - start_date).days + 1
        leave_request.duration_days = days_requested
        
        # Déterminer le niveau de validation nécessaire
        profile = self.request.user.employee_profile
        if profile.role == 'employee':
            # Employé : validation par manager puis RH/DG
            leave_request.status = 'pending'
            leave_request.manager = profile.manager
        elif profile.role == 'manager':
            # Manager : validation directe par RH/DG
            leave_request.status = 'approved_manager'
        elif profile.role == 'rh_dg':
            # RH/DG : auto-approbation
            leave_request.status = 'approved_rh'
        
        leave_request.save()
        
        # Déclencher les notifications (sera géré par les signaux)
        pass
        
        messages.success(self.request, 'Demande de congé créée avec succès.')
        return redirect(self.get_success_url())


class LeaveApprovalListView(LoginRequiredMixin, ListView):
    """
    Liste des demandes de congés à valider pour les managers et RH/DG.
    """
    model = LeaveRequest
    template_name = 'leave/leave_approval_list.html'
    context_object_name = 'leave_requests'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        profile = user.employee_profile
        
        if profile.role == 'manager':
            # Manager : voir les demandes de ses employés
            managed_employees = User.objects.filter(
                employee_profile__manager=user
            )
            queryset = LeaveRequest.objects.filter(
                employee__in=managed_employees,
                status='pending'
            ).select_related('employee', 'leave_type', 'employee__employee_profile')
        elif profile.role == 'rh_dg':
            # RH/DG : voir toutes les demandes en attente de validation finale
            queryset = LeaveRequest.objects.filter(
                status='approved_manager'
            ).select_related('employee', 'leave_type', 'employee__employee_profile')
        else:
            queryset = LeaveRequest.objects.none()
        
        return queryset.order_by('-created_at')


class LeaveApprovalDetailView(LoginRequiredMixin, DetailView):
    """
    Détail d'une demande de congé pour validation.
    """
    model = LeaveRequest
    template_name = 'leave/leave_approval_detail.html'
    context_object_name = 'leave_request'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['approval_form'] = LeaveApprovalForm()
        return context


class LeaveApprovalUpdateView(LoginRequiredMixin, UpdateView):
    """
    Traitement d'une demande de congé (approbation/rejet).
    """
    model = LeaveRequest
    form_class = LeaveApprovalForm
    template_name = 'leave/leave_approval_detail.html'
    
    def form_valid(self, form):
        leave_request = form.save(commit=False)
        user = self.request.user
        profile = user.employee_profile
        action = form.cleaned_data['action']
        comment = form.cleaned_data.get('comment', '')
        
        with transaction.atomic():
            if profile.role == 'manager':
                # Validation manager
                if action == 'approve':
                    leave_request.manager_decision = 'approved_manager'
                    leave_request.manager_comment = comment
                    leave_request.manager_decision_at = timezone.now()
                    leave_request.status = 'approved_manager'
                    
                else:  # reject
                    leave_request.manager_decision = 'rejected_manager'
                    leave_request.manager_comment = comment
                    leave_request.manager_decision_at = timezone.now()
                    leave_request.status = 'rejected_manager'
            
            elif profile.role == 'rh_dg':
                # Validation RH/DG
                if action == 'approve':
                    leave_request.rh_decision = 'approved_rh'
                    leave_request.rh_comment = comment
                    leave_request.rh_decision_at = timezone.now()
                    leave_request.status = 'approved_rh'
                    
                    # Déduire du solde
                    self._deduct_leave_balance(leave_request)
                else:  # reject
                    leave_request.rh_decision = 'rejected_rh'
                    leave_request.rh_comment = comment
                    leave_request.rh_decision_at = timezone.now()
                    leave_request.status = 'rejected_rh'
            
            leave_request.save()
        
        # Déclencher les notifications
        from notifications.services import NotificationService
        NotificationService.send_leave_notifications(leave_request, action)
        
        # Messages de succès
        if action == 'approve':
            messages.success(self.request, 'Demande de congé approuvée avec succès.')
        else:
            messages.success(self.request, 'Demande de congé rejetée.')
        
        return redirect('leave:leave_approval_list')
    
    def _needs_rh_approval(self, leave_request):
        """Détermine si une validation RH/DG est nécessaire."""
        # Logique métier : validation RH/DG requise pour certains types de congés
        return leave_request.leave_type.requires_rh_approval
    
    def _deduct_leave_balance(self, leave_request):
        """Déduit les jours de congé du solde de l'employé."""
        days_requested = (leave_request.end_date - leave_request.start_date).days + 1
        
        balance, created = LeaveBalance.objects.get_or_create(
            employee=leave_request.employee,
            leave_type=leave_request.leave_type,
            year=leave_request.start_date.year,
            defaults={'allocated_balance': leave_request.leave_type.allocation_amount, 'taken_balance': 0}
        )
        
        balance.taken_balance += days_requested
        balance.save()


class LeaveBalanceListView(LoginRequiredMixin, ListView):
    """
    Liste des soldes de congés pour l'utilisateur connecté.
    """
    model = LeaveBalance
    template_name = 'leave/leave_balance_list.html'
    context_object_name = 'leave_balances'
    
    def get_queryset(self):
        current_year = date.today().year
        return LeaveBalance.objects.filter(
            employee=self.request.user,
            year=current_year
        ).select_related('leave_type')


def leave_statistics_api(request):
    """
    API pour les statistiques de congés (pour les dashboards).
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    
    user = request.user
    profile = user.employee_profile
    current_year = date.today().year
    
    stats = {
        'total_requests': 0,
        'pending_requests': 0,
        'approved_requests': 0,
        'rejected_requests': 0,
        'available_days': 0,
        'used_days': 0,
    }
    
    if profile.role == 'employee':
        # Statistiques pour un employé
        leave_requests = LeaveRequest.objects.filter(employee=user)
        stats['total_requests'] = leave_requests.count()
        stats['pending_requests'] = leave_requests.filter(status='pending').count()
        stats['approved_requests'] = leave_requests.filter(status__in=['approved_manager', 'approved_rh']).count()
        stats['rejected_requests'] = leave_requests.filter(status__in=['rejected_manager', 'rejected_rh']).count()
        
        # Soldes
        balances = LeaveBalance.objects.filter(
            employee=user,
            year=current_year
        )
        stats['available_days'] = sum(b.remaining_balance for b in balances)
        stats['used_days'] = sum(b.taken_balance for b in balances)
    
    elif profile.role == 'manager':
        # Statistiques pour un manager (son équipe)
        managed_employees = User.objects.filter(
            employee_profile__manager=user
        )
        
        leave_requests = LeaveRequest.objects.filter(
            employee__in=managed_employees
        )
        stats['total_requests'] = leave_requests.count()
        stats['pending_requests'] = leave_requests.filter(status='pending').count()
        stats['approved_requests'] = leave_requests.filter(status__in=['approved_manager', 'approved_rh']).count()
        stats['rejected_requests'] = leave_requests.filter(status__in=['rejected_manager', 'rejected_rh']).count()
    
    elif profile.role == 'rh_dg':
        # Statistiques pour RH/DG (toute l'entreprise)
        leave_requests = LeaveRequest.objects.all()
        stats['total_requests'] = leave_requests.count()
        stats['pending_requests'] = leave_requests.filter(status='approved_manager').count()
        stats['approved_requests'] = leave_requests.filter(status='approved_rh').count()
        stats['rejected_requests'] = leave_requests.filter(status__in=['rejected_manager', 'rejected_rh']).count()
    
    return JsonResponse(stats)
