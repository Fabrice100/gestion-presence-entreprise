"""
Vues pour la gestion des heures supplémentaires.

Ce module contient les vues Django pour :
- OvertimeRequestListView : Liste des demandes d'heures supplémentaires
- OvertimeRequestCreateView : Création d'une demande
- OvertimeRequestDetailView : Détail d'une demande
- OvertimeApprovalListView : Liste des validations à effectuer
- OvertimeApprovalProcessView : Traitement d'une validation

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import OvertimeRequest, OvertimeConfiguration
from .overtime_forms import OvertimeRequestForm, OvertimeApprovalForm
from accounts.models import EmployeeProfile
from notifications.services import NotificationService


# Mixins pour les permissions
class EmployeeRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.employee_profile.role == 'employee'

    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('dashboard:dashboard')


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.employee_profile.role == 'manager'

    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('dashboard:dashboard')


class HRDGDRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.employee_profile.is_rh_dg()

    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('dashboard:dashboard')


class OvertimeRequestListView(LoginRequiredMixin, ListView):
    """
    Vue pour lister les demandes d'heures supplémentaires selon le rôle.
    """
    model = OvertimeRequest
    template_name = 'attendance/overtime_request_list.html'
    context_object_name = 'overtime_requests'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        profile = user.employee_profile
        
        if profile.role == 'employee':
            # L'employé voit ses propres demandes
            return OvertimeRequest.objects.filter(employee=user).order_by('-created_at')
        elif profile.role == 'manager':
            # Le manager voit les demandes de ses employés
            managed_employees = User.objects.filter(employee_profile__manager=user)
            return OvertimeRequest.objects.filter(employee__in=managed_employees).order_by('-created_at')
        elif profile.is_rh_dg():
            # RH/DG voit toutes les demandes
            return OvertimeRequest.objects.all().order_by('-created_at')
        else:
            return OvertimeRequest.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Statistiques pour le dashboard
        context['stats'] = {
            'total_requests': self.get_queryset().count(),
            'pending_requests': self.get_queryset().filter(status='pending').count(),
            'approved_requests': self.get_queryset().filter(status='approved').count(),
            'rejected_requests': self.get_queryset().filter(status='rejected').count(),
        }
        
        # Filtres disponibles
        context['overtime_types'] = OvertimeRequest.OVERTIME_TYPE_CHOICES
        context['status_choices'] = OvertimeRequest.STATUS_CHOICES
        
        return context


class OvertimeRequestCreateView(EmployeeRequiredMixin, CreateView):
    """
    Vue pour créer une nouvelle demande d'heures supplémentaires.
    """
    model = OvertimeRequest
    form_class = OvertimeRequestForm
    template_name = 'attendance/overtime_request_create.html'
    success_url = reverse_lazy('attendance:overtime_request_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Définir l'employé et calculer les heures automatiquement
        form.instance.employee = self.request.user
        form.instance.hours_requested = form.instance.calculate_hours()
        
        # Déterminer le manager
        if self.request.user.employee_profile.manager:
            form.instance.manager = self.request.user.employee_profile.manager
        
        response = super().form_valid(form)
        
        # Envoyer notification au manager
        if form.instance.manager:
            NotificationService.send_overtime_request_notification(form.instance)
        
        messages.success(
            self.request,
            f"Votre demande d'heures supplémentaires pour le {form.instance.date} a été soumise avec succès."
        )
        
        return response


class OvertimeRequestDetailView(LoginRequiredMixin, DetailView):
    """
    Vue pour afficher le détail d'une demande d'heures supplémentaires.
    """
    model = OvertimeRequest
    template_name = 'attendance/overtime_request_detail.html'
    context_object_name = 'overtime_request'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.get_object()
        user = self.request.user
        
        # Vérifier si l'utilisateur peut valider cette demande
        context['can_approve'] = False
        context['approval_role'] = None
        
        if user.employee_profile.role == 'manager' and request.manager == user:
            context['can_approve'] = True
            context['approval_role'] = 'manager'
        elif user.employee_profile.is_rh_dg():
            context['can_approve'] = True
            context['approval_role'] = 'rh_dg'
        
        # Formulaires de validation
        context['approval_form'] = OvertimeApprovalForm()
        
        return context


class OvertimeApprovalListView(LoginRequiredMixin, ListView):
    """
    Vue pour lister les demandes d'heures supplémentaires à valider.
    """
    model = OvertimeRequest
    template_name = 'attendance/overtime_approval_list.html'
    context_object_name = 'pending_requests'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        profile = user.employee_profile
        
        if profile.role == 'manager':
            # Demandes des employés du manager en attente de validation manager
            managed_employees = User.objects.filter(employee_profile__manager=user)
            return OvertimeRequest.objects.filter(
                employee__in=managed_employees,
                status='pending',
                manager_decision__isnull=True
            ).order_by('-created_at')
        elif profile.is_rh_dg():
            # Demandes approuvées par le manager en attente de validation RH/DG
            return OvertimeRequest.objects.filter(
                manager_decision='approved',
                rh_decision__isnull=True,
                status='pending'
            ).order_by('-created_at')
        else:
            return OvertimeRequest.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Statistiques des validations en attente
        context['stats'] = {
            'pending_manager': 0,
            'pending_rh': 0,
            'total_pending': 0
        }
        
        if user.employee_profile.role == 'manager':
            managed_employees = User.objects.filter(employee_profile__manager=user)
            context['stats']['pending_manager'] = OvertimeRequest.objects.filter(
                employee__in=managed_employees,
                status='pending',
                manager_decision__isnull=True
            ).count()
            context['stats']['total_pending'] = context['stats']['pending_manager']
        elif user.employee_profile.is_rh_dg():
            context['stats']['pending_rh'] = OvertimeRequest.objects.filter(
                manager_decision='approved',
                rh_decision__isnull=True,
                status='pending'
            ).count()
            context['stats']['total_pending'] = context['stats']['pending_rh']
        
        return context


class OvertimeApprovalProcessView(LoginRequiredMixin, View):
    """
    Vue pour traiter une validation de demande d'heures supplémentaires.
    """
    def post(self, request, pk):
        overtime_request = get_object_or_404(OvertimeRequest, pk=pk)
        user = request.user
        decision = request.POST.get('decision')
        comment = request.POST.get('comment', '')
        
        # Vérifier les permissions
        can_approve = False
        approval_role = None
        
        if user.employee_profile.role == 'manager' and overtime_request.manager == user:
            can_approve = True
            approval_role = 'manager'
        elif user.employee_profile.is_rh_dg():
            can_approve = True
            approval_role = 'rh_dg'
        
        if not can_approve:
            messages.error(request, "Vous n'avez pas les permissions pour valider cette demande.")
            return redirect('attendance:overtime_request_detail', pk=pk)
        
        # Traiter la validation
        with transaction.atomic():
            if approval_role == 'manager':
                overtime_request.manager_decision = decision
                overtime_request.manager_comment = comment
                overtime_request.manager_decision_at = timezone.now()
                
                # Si rejeté par le manager, finaliser la demande
                if decision == 'rejected':
                    overtime_request.status = 'rejected'
                    overtime_request.rh_decision = 'rejected'
                    overtime_request.rh_decision_at = timezone.now()
                
            elif approval_role == 'rh_dg':
                overtime_request.rh_decision = decision
                overtime_request.rh_comment = comment
                overtime_request.rh_decision_at = timezone.now()
                
                # Finaliser le statut
                if decision == 'approved':
                    overtime_request.status = 'approved'
                else:
                    overtime_request.status = 'rejected'
            
            overtime_request.save()
            
            # Envoyer notifications
            NotificationService.send_overtime_approval_notification(overtime_request, decision, approval_role)
        
        # Messages de confirmation
        if decision == 'approved':
            messages.success(request, f"La demande d'heures supplémentaires a été approuvée.")
        else:
            messages.warning(request, f"La demande d'heures supplémentaires a été rejetée.")
        
        return redirect('attendance:overtime_approval_list')




def get_overtime_stats_api(request):
    """
    API pour obtenir les statistiques des heures supplémentaires.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Non authentifié'}, status=401)
    
    user = request.user
    profile = user.employee_profile
    
    # Statistiques selon le rôle
    if profile.role == 'employee':
        requests = OvertimeRequest.objects.filter(employee=user)
    elif profile.role == 'manager':
        managed_employees = User.objects.filter(employee_profile__manager=user)
        requests = OvertimeRequest.objects.filter(employee__in=managed_employees)
    elif profile.is_rh_dg():
        requests = OvertimeRequest.objects.all()
    else:
        requests = OvertimeRequest.objects.none()
    
    stats = {
        'requests': {
            'total': requests.count(),
            'pending': requests.filter(status='pending').count(),
            'approved': requests.filter(status='approved').count(),
            'rejected': requests.filter(status='rejected').count(),
        }
    }
    
    return JsonResponse(stats)
