"""
Vues pour la gestion des heures supplémentaires.

Ce module contient les vues Django pour :
- Consultation des enregistrements d'heures supplémentaires
- Validation des enregistrements par les managers et RH/DG
- Configuration des règles d'heures supplémentaires

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from .models import OvertimeRecord, OvertimeConfiguration
from .overtime_forms import OvertimeRecordForm, OvertimeApprovalForm
from accounts.models import EmployeeProfile


# Mixins pour les permissions

class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin pour vérifier si l'utilisateur est un manager."""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.employee_profile.is_manager()
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('dashboard:dashboard')


class RHRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin pour vérifier si l'utilisateur est RH/DG."""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.employee_profile.is_rh_dg()
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return redirect('dashboard:dashboard')


# Vues pour les enregistrements d'heures supplémentaires

class OvertimeRecordListView(LoginRequiredMixin, ListView):
    """
    Vue pour lister les enregistrements d'heures supplémentaires.
    """
    model = OvertimeRecord
    template_name = 'attendance/overtime_record_list.html'
    context_object_name = 'records'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        profile = user.employee_profile
        
        if profile.role == 'employee':
            # L'employé voit ses propres enregistrements
            return OvertimeRecord.objects.filter(employee=user).order_by('-date')
        elif profile.role == 'manager':
            # Le manager voit les enregistrements de ses employés
            managed_employees = User.objects.filter(employee_profile__manager=user)
            return OvertimeRecord.objects.filter(employee__in=managed_employees).order_by('-date')
        elif profile.is_rh_dg():
            # RH/DG voit tous les enregistrements
            return OvertimeRecord.objects.all().order_by('-date')
        else:
            return OvertimeRecord.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        queryset = self.get_queryset()
        context['stats'] = {
            'total_records': queryset.count(),
            'detected_records': queryset.filter(status='detected').count(),
            'pending_approval': queryset.filter(status='pending_approval').count(),
            'approved_records': queryset.filter(status='approved').count(),
            'rejected_records': queryset.filter(status='rejected').count(),
            'total_overtime_hours': queryset.aggregate(
                total=Sum('overtime_hours')
            )['total'] or Decimal('0.00'),
        }
        
        return context


class OvertimeRecordDetailView(LoginRequiredMixin, DetailView):
    """
    Vue pour afficher les détails d'un enregistrement d'heures supplémentaires.
    """
    model = OvertimeRecord
    template_name = 'attendance/overtime_record_detail.html'
    context_object_name = 'record'

    def get_queryset(self):
        user = self.request.user
        profile = user.employee_profile
        
        if profile.role == 'employee':
            # L'employé voit ses propres enregistrements
            return OvertimeRecord.objects.filter(employee=user)
        elif profile.role == 'manager':
            # Le manager voit les enregistrements de ses employés
            managed_employees = User.objects.filter(employee_profile__manager=user)
            return OvertimeRecord.objects.filter(employee__in=managed_employees)
        elif profile.is_rh_dg():
            # RH/DG voit tous les enregistrements
            return OvertimeRecord.objects.all()
        else:
            return OvertimeRecord.objects.none()


class OvertimeApprovalListView(LoginRequiredMixin, ListView):
    """
    Vue pour lister les enregistrements en attente de validation.
    """
    model = OvertimeRecord
    template_name = 'attendance/overtime_approval_list.html'
    context_object_name = 'records'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        profile = user.employee_profile
        
        if profile.role == 'manager':
            # Le manager voit les enregistrements de ses employés en attente
            managed_employees = User.objects.filter(employee_profile__manager=user)
            return OvertimeRecord.objects.filter(
                employee__in=managed_employees,
                status__in=['detected', 'pending_approval']
            ).order_by('-date')
        elif profile.is_rh_dg():
            # RH/DG voit tous les enregistrements en attente
            return OvertimeRecord.objects.filter(
                status__in=['detected', 'pending_approval']
            ).order_by('-date')
        else:
            return OvertimeRecord.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        queryset = self.get_queryset()
        context['stats'] = {
            'total_pending': queryset.count(),
            'detected_records': queryset.filter(status='detected').count(),
            'pending_approval': queryset.filter(status='pending_approval').count(),
        }
        
        return context


class OvertimeApprovalProcessView(LoginRequiredMixin, UpdateView):
    """
    Vue pour traiter la validation d'un enregistrement d'heures supplémentaires.
    """
    model = OvertimeRecord
    form_class = OvertimeApprovalForm
    template_name = 'attendance/overtime_approval_process.html'
    context_object_name = 'record'

    def get_queryset(self):
        user = self.request.user
        profile = user.employee_profile
        
        if profile.role == 'manager':
            # Le manager peut valider les enregistrements de ses employés
            managed_employees = User.objects.filter(employee_profile__manager=user)
            return OvertimeRecord.objects.filter(employee__in=managed_employees)
        elif profile.is_rh_dg():
            # RH/DG peut valider tous les enregistrements
            return OvertimeRecord.objects.all()
        else:
            return OvertimeRecord.objects.none()

    def form_valid(self, form):
        record = self.get_object()
        user = self.request.user
        decision = form.cleaned_data['decision']
        comment = form.cleaned_data['comment']
        
        # Déterminer si c'est le manager ou le RH/DG qui valide
        is_manager = user.employee_profile.is_manager()
        is_rh_dg = user.employee_profile.is_rh_dg()
        
        with transaction.atomic():
            if is_manager and record.manager == user:
                # Validation manager
                record.manager_decision = decision
                record.manager_comment = comment
                record.manager_decision_at = timezone.now()
                
                if decision == 'approved':
                    record.status = 'pending_approval'  # En attente RH/DG
                elif decision == 'rejected':
                    record.status = 'rejected'
                elif decision == 'disputed':
                    record.status = 'disputed'
                
                record.save()
                
                # TODO: Notification RH/DG (à implémenter avec emails)
                
                messages.success(self.request, f"L'enregistrement a été {decision} par le manager.")
                
            elif is_rh_dg:
                # Validation RH/DG
                record.rh_decision = decision
                record.rh_comment = comment
                record.rh_decision_at = timezone.now()
                
                if decision == 'approved':
                    record.status = 'approved'
                elif decision == 'rejected':
                    record.status = 'rejected'
                elif decision == 'disputed':
                    record.status = 'disputed'
                
                record.save()
                
                # TODO: Notification employé (à implémenter avec emails)
                
                messages.success(self.request, f"L'enregistrement a été {decision} par les RH/DG.")
        
        return redirect('attendance:overtime_approval_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajouter des informations sur les pointages associés
        record = self.get_object()
        context['attendance_records'] = record.attendance_records.all()
        
        return context


# API pour les statistiques

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
        records = OvertimeRecord.objects.filter(employee=user)
    elif profile.role == 'manager':
        managed_employees = User.objects.filter(employee_profile__manager=user)
        records = OvertimeRecord.objects.filter(employee__in=managed_employees)
    elif profile.is_rh_dg():
        records = OvertimeRecord.objects.all()
    else:
        records = OvertimeRecord.objects.none()
    
    stats = {
        'records': {
            'total': records.count(),
            'detected': records.filter(status='detected').count(),
            'pending_approval': records.filter(status='pending_approval').count(),
            'approved': records.filter(status='approved').count(),
            'rejected': records.filter(status='rejected').count(),
        },
        'hours': {
            'total_overtime': float(records.aggregate(
                total=Sum('overtime_hours')
            )['total'] or Decimal('0.00')),
            'total_normal': float(records.aggregate(
                total=Sum('normal_hours')
            )['total'] or Decimal('0.00')),
        }
    }
    
    return JsonResponse(stats)