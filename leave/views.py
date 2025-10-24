"""
Vues pour l'application leave (congés et absences).

Ce module contient les vues pour :
- Demande de congés
- Validation des congés
- Consultation des soldes
- Gestion des types de congés

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q

from .models import LeaveRequest, LeaveBalance, LeaveType, Holiday

# Import du mixin centralisé (principe DRY)
from common.mixins import EnhancedLoginRequiredMixin, EmployeeRequiredMixin


class LeaveRequestListView(EmployeeRequiredMixin, ListView):
    """Vue pour lister les demandes de congés."""
    model = LeaveRequest
    template_name = 'leave/leave_request_list.html'
    context_object_name = 'leave_requests'
    
    def get_queryset(self):
        return LeaveRequest.objects.filter(employee=self.request.user)


class LeaveRequestCreateView(EmployeeRequiredMixin, TemplateView):
    """Vue pour créer une demande de congé."""
    template_name = 'leave/leave_request_create.html'


class LeaveBalanceListView(EmployeeRequiredMixin, ListView):
    """Vue pour lister les soldes de congés."""
    model = LeaveBalance
    template_name = 'leave/leave_balance_list.html'
    context_object_name = 'leave_balances'
    
    def get_queryset(self):
        return LeaveBalance.objects.filter(employee=self.request.user)


class RHLeaveManagementView(EnhancedLoginRequiredMixin, ListView):
    """Vue pour que les RH/DG gèrent toutes les demandes de congés."""
    model = LeaveRequest
    template_name = 'leave/rh_leave_management.html'
    context_object_name = 'leave_requests'
    paginate_by = 15
    
    def get_queryset(self):
        """Filtre toutes les demandes pour les RH/DG."""
        queryset = LeaveRequest.objects.all().select_related(
            'employee', 'leave_type', 'employee__employee_profile__department'
        ).order_by('-created_at')
        
        # Filtres
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        leave_type = self.request.GET.get('leave_type')
        if leave_type:
            queryset = queryset.filter(leave_type_id=leave_type)
            
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(employee__employee_profile__department_id=department)
            
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajoute des données de contexte."""
        context = super().get_context_data(**kwargs)
        
        # Statistiques globales
        all_requests = LeaveRequest.objects.all()
        context['total_requests'] = all_requests.count()
        context['pending_requests'] = all_requests.filter(status='pending').count()
        context['approved_requests'] = all_requests.filter(status='approved').count()
        context['rejected_requests'] = all_requests.filter(status='rejected').count()
        context['this_month_requests'] = all_requests.filter(
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year
        ).count()
        
        # Statistiques par département
        from accounts.models import Department
        departments = Department.objects.all()
        context['department_stats'] = [
            {
                'department': dept,
                'total': all_requests.filter(employee__employee_profile__department=dept).count(),
                'pending': all_requests.filter(employee__employee_profile__department=dept, status='pending').count(),
                'approved': all_requests.filter(employee__employee_profile__department=dept, status='approved').count(),
            }
            for dept in departments
        ]
        
        # Données pour les filtres
        context['leave_types'] = LeaveType.objects.filter(is_active=True)
        context['departments'] = departments
        context['employees'] = User.objects.filter(
            leave_requests__isnull=False
        ).distinct().select_related('employee_profile')
        
        return context


class RHLeaveReportsView(EnhancedLoginRequiredMixin, TemplateView):
    """Vue pour les rapports RH/DG sur les congés."""
    template_name = 'leave/rh_leave_reports.html'
    
    def get_context_data(self, **kwargs):
        """Ajoute des données de contexte pour les rapports."""
        context = super().get_context_data(**kwargs)
        
        # Statistiques par mois (12 derniers mois)
        from datetime import datetime, timedelta
        from django.db.models import Count
        
        months_data = []
        for i in range(12):
            month_date = timezone.now().date() - timedelta(days=30*i)
            month_requests = LeaveRequest.objects.filter(
                created_at__year=month_date.year,
                created_at__month=month_date.month
            )
            
            months_data.append({
                'month': month_date.strftime('%Y-%m'),
                'month_name': month_date.strftime('%B %Y'),
                'total': month_requests.count(),
                'approved': month_requests.filter(status='approved').count(),
                'rejected': month_requests.filter(status='rejected').count(),
                'pending': month_requests.filter(status='pending').count(),
            })
        
        context['monthly_stats'] = months_data
        
        # Top des types de congés
        context['top_leave_types'] = LeaveRequest.objects.values(
            'leave_type__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Employés avec le plus de congés
        context['top_employees'] = User.objects.filter(
            leave_requests__isnull=False
        ).annotate(
            total_leaves=Count('leave_requests'),
            approved_leaves=Count('leave_requests', filter=Q(leave_requests__status='approved'))
        ).order_by('-total_leaves')[:10]
        
        return context


class ManagerLeaveRequestsView(EnhancedLoginRequiredMixin, ListView):
    """Vue pour que le manager voie ses propres demandes."""
    model = LeaveRequest
    template_name = 'leave/manager_my_requests.html'
    context_object_name = 'leave_requests'
    paginate_by = 12
    
    def get_queryset(self):
        """Filtre les demandes du manager connecté."""
        queryset = LeaveRequest.objects.filter(
            employee=self.request.user
        ).select_related('leave_type').order_by('-created_at')
        
        # Filtres
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        leave_type = self.request.GET.get('leave_type')
        if leave_type:
            queryset = queryset.filter(leave_type_id=leave_type)
            
        year = self.request.GET.get('year')
        if year:
            queryset = queryset.filter(start_date__year=year)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajoute des données de contexte."""
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        queryset = self.get_queryset()
        context['total_requests'] = queryset.count()
        context['pending_requests'] = queryset.filter(status='pending').count()
        context['approved_requests'] = queryset.filter(status='approved').count()
        
        # Solde restant (utiliser le service)
        from .leave_balance_service import leave_balance_service
        context['remaining_days'] = leave_balance_service.get_remaining_balance(self.request.user)
        
        # Données pour les filtres
        context['leave_types'] = LeaveType.objects.filter(is_active=True)
        context['available_years'] = range(2020, timezone.now().year + 2)
        
        return context


class ManagerLeaveValidationView(EnhancedLoginRequiredMixin, ListView):
    """Vue pour que le manager valide les demandes des autres."""
    model = LeaveRequest
    template_name = 'leave/manager_validation.html'
    context_object_name = 'leave_requests'
    paginate_by = 12
    
    def get_queryset(self):
        """Filtre les demandes en attente de validation."""
        queryset = LeaveRequest.objects.filter(
            status='pending'
        ).exclude(employee=self.request.user).select_related('employee', 'leave_type', 'employee__employee_profile__department').order_by('-created_at')
        
        # Filtres
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
            
        leave_type = self.request.GET.get('leave_type')
        if leave_type:
            queryset = queryset.filter(leave_type_id=leave_type)
            
        employee = self.request.GET.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajoute des données de contexte."""
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        all_requests = LeaveRequest.objects.exclude(employee=self.request.user)
        context['pending_count'] = all_requests.filter(status='pending').count()
        context['approved_count'] = all_requests.filter(status='approved').count()
        context['rejected_count'] = all_requests.filter(status='rejected').count()
        context['total_this_month'] = all_requests.filter(
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year
        ).count()
        
        # Données pour les filtres
        context['leave_types'] = LeaveType.objects.filter(is_active=True)
        context['employees'] = User.objects.filter(
            leave_requests__isnull=False
        ).distinct().select_related('employee_profile')
        
        return context


class LeaveTypeListView(EnhancedLoginRequiredMixin, ListView):
    """Vue pour lister les types de congés."""
    model = LeaveType
    template_name = 'leave/leave_type_list.html'
    context_object_name = 'leave_types'


class HolidayListView(EnhancedLoginRequiredMixin, ListView):
    """Vue pour lister les jours fériés."""
    model = Holiday
    template_name = 'leave/holiday_list.html'
    context_object_name = 'holidays'


# Vues temporaires pour éviter les erreurs 404
class LeaveRequestDetailView(EmployeeRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveRequestEditView(EmployeeRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveRequestCancelView(EmployeeRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveApprovalView(EnhancedLoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveRejectionView(EnhancedLoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveBalanceDetailView(EmployeeRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveTypeDetailView(EnhancedLoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class HolidayDetailView(EnhancedLoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveReportView(EnhancedLoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveCalendarView(EmployeeRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'