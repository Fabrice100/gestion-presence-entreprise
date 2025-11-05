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
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from django.urls import reverse

from .models import LeaveRequest, LeaveBalance, LeaveType, Holiday
from accounts.models import Department

# Import du mixin centralisé (principe DRY)
from common.mixins import EnhancedLoginRequiredMixin, EmployeeRequiredMixin

# Note: LeaveRequestCreateView et LeaveBalanceListView sont dans workflow_views.py


class RHLeaveManagementView(EnhancedLoginRequiredMixin, ListView):
    """Vue pour que les RH gèrent toutes les demandes de congés."""
    model = LeaveRequest
    template_name = 'leave/rh_leave_management_ultra_modern.html'
    context_object_name = 'leave_requests'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtre toutes les demandes pour les RH."""
        queryset = LeaveRequest.objects.all().select_related(
            'employee', 'leave_type', 'employee__employeeprofile'
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
            queryset = queryset.filter(employee__employeeprofile__department=department)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(employee__employeeprofile__employee_id__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajoute des données de contexte."""
        context = super().get_context_data(**kwargs)
        
        # Statistiques globales
        all_requests = LeaveRequest.objects.all()
        context['stats'] = {
            'pending_count': all_requests.filter(status='approved_manager').count(),
            'approved_count': all_requests.filter(status='approved_rh').count(),
            'rejected_count': all_requests.filter(status__in=['rejected_manager', 'rejected_rh']).count(),
            'this_month_count': all_requests.filter(
                created_at__month=timezone.now().month,
                created_at__year=timezone.now().year
            ).count(),
        }
        
        # Départements et types de congés pour filtres
        from accounts.models import EmployeeProfile
        context['departments'] = EmployeeProfile.objects.values_list('department', flat=True).distinct()
        context['leave_types'] = LeaveType.objects.all()
        
        return context


class RHLeaveReportsView(EnhancedLoginRequiredMixin, TemplateView):
    """Vue pour les rapports RH sur les congés."""
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
    template_name = 'leave/manager_my_requests_ultra_modern.html'
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
    template_name = 'leave/manager_validation_ultra_modern.html'
    context_object_name = 'leave_requests'
    paginate_by = 12
    
    def get_queryset(self):
        """
        Filtre les demandes en attente de validation.
        
        FILTRAGE STRICT PAR DÉPARTEMENT (conforme aux spécifications):
        Le Manager voit SEULEMENT les demandes de son département/service.
        """
        # Récupérer le département du Manager
        manager_profile = self.request.user.employee_profile
        manager_department = manager_profile.department
        
        if not manager_department:
            # Manager sans département : aucune demande
            return LeaveRequest.objects.none()
        
        # FILTRAGE STRICT: seulement département du Manager
        queryset = LeaveRequest.objects.filter(
            status='pending',
            employee__employee_profile__department=manager_department
        ).exclude(
            employee=self.request.user  # Exclure propres demandes Manager
        ).select_related(
            'employee', 
            'leave_type', 
            'employee__employee_profile__department'
        ).order_by('-created_at')
        
        # Filtres
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
        
        # FILTRAGE STRICT PAR DÉPARTEMENT (conforme aux spécifications)
        manager_profile = self.request.user.employee_profile
        manager_department = manager_profile.department
        
        if not manager_department:
            # Manager sans département
            all_requests = LeaveRequest.objects.none()
            context['employees'] = User.objects.none()
        else:
            # Seulement département du Manager
            all_requests = LeaveRequest.objects.filter(
                employee__employee_profile__department=manager_department
            ).exclude(employee=self.request.user)
            
            # Employés du département uniquement
            context['employees'] = User.objects.filter(
                employee_profile__department=manager_department,
                leave_requests__isnull=False
            ).exclude(id=self.request.user.id).distinct().select_related('employee_profile')
        
        # Statistiques (seulement département)
        context['pending_count'] = all_requests.filter(status='pending').count()
        context['approved_count'] = all_requests.filter(status__in=['approved_manager', 'approved_rh']).count()
        context['rejected_count'] = all_requests.filter(status__in=['rejected_manager', 'rejected_rh']).count()
        context['monthly_count'] = all_requests.filter(
            created_at__month=timezone.now().month,
            created_at__year=timezone.now().year
        ).count()
        
        # Données pour les filtres
        context['leave_types'] = LeaveType.objects.filter(is_active=True)
        
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


# Vues détaillées avec templates complets
class LeaveRequestDetailView(EmployeeRequiredMixin, DetailView):
    model = LeaveRequest
    template_name = 'leave/leave_request_detail.html'
    context_object_name = 'leave_request'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .leave_balance_service import leave_balance_service
        context['remaining_days'] = leave_balance_service.get_remaining_balance(self.request.user)
        return context


class LeaveRequestEditView(EmployeeRequiredMixin, UpdateView):
    model = LeaveRequest
    template_name = 'leave/leave_request_edit.html'
    context_object_name = 'leave_request'
    fields = ['leave_type', 'start_date', 'end_date', 'reason', 'justification']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .leave_balance_service import leave_balance_service
        context['remaining_days'] = leave_balance_service.get_remaining_balance(self.request.user)
        context['leave_types'] = LeaveType.objects.filter(is_active=True)
        return context
    
    def get_success_url(self):
        return reverse('leave:leave_request_detail', kwargs={'pk': self.object.pk})


class LeaveRequestCancelView(EmployeeRequiredMixin, DetailView):
    model = LeaveRequest
    context_object_name = 'leave_request'

    # Annuler immédiatement (GET) et rediriger sans template intermédiaire
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.status = 'cancelled'
        # Historiser la raison si fournie via query string
        reason = request.GET.get('reason') or ''
        if reason:
            self.object.manager_comment = f"Annulé par l'employé: {reason}"
        self.object.save()
        messages.success(request, 'Demande de congé annulée avec succès.')
        return redirect('leave:leave_request_list')

    # Support POST optionnel (même logique)
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        reason = request.POST.get('cancellation_reason') or ''
        self.object.status = 'cancelled'
        if reason:
            self.object.manager_comment = f"Annulé par l'employé: {reason}"
        self.object.save()
        messages.success(request, 'Demande de congé annulée avec succès.')
        return redirect('leave:leave_request_list')




class LeaveBalanceDetailView(EmployeeRequiredMixin, DetailView):
    model = LeaveBalance
    template_name = 'leave/leave_balance_detail.html'
    context_object_name = 'leave_balance'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['remaining_days'] = self.object.remaining_balance
        return context


class LeaveTypeDetailView(EnhancedLoginRequiredMixin, DetailView):
    model = LeaveType
    template_name = 'leave/leave_type_detail.html'
    context_object_name = 'leave_type'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Statistiques d'utilisation
        context['total_requests'] = LeaveRequest.objects.filter(leave_type=self.object).count()
        context['approved_requests'] = LeaveRequest.objects.filter(leave_type=self.object, status__in=['approved_manager', 'approved_rh']).count()
        return context


class HolidayDetailView(EnhancedLoginRequiredMixin, DetailView):
    model = Holiday
    template_name = 'leave/holiday_detail.html'
    context_object_name = 'holiday'


class LeaveReportView(EnhancedLoginRequiredMixin, TemplateView):
    template_name = 'leave/leave_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .leave_balance_service import leave_balance_service
        
        # Filtres
        year = self.request.GET.get('year', timezone.now().year)
        department = self.request.GET.get('department')
        leave_type = self.request.GET.get('leave_type')
        
        # Statistiques globales
        queryset = LeaveRequest.objects.filter(start_date__year=year)
        if department:
            queryset = queryset.filter(employee__employee_profile__department_id=department)
        if leave_type:
            queryset = queryset.filter(leave_type_id=leave_type)
        
        context.update({
            'selected_year': int(year),
            'available_years': range(2020, timezone.now().year + 2),
            'departments': Department.objects.all(),
            'leave_types': LeaveType.objects.filter(is_active=True),
            'total_requests': queryset.count(),
            'approved_requests': queryset.filter(status__in=['approved_manager', 'approved_rh']).count(),
            'pending_requests': queryset.filter(status='pending').count(),
            'rejected_requests': queryset.filter(status__in=['rejected_manager', 'rejected_rh']).count(),
            'cancelled_requests': queryset.filter(status='cancelled').count(),
        })
        
        return context


class LeaveCalendarView(EmployeeRequiredMixin, TemplateView):
    template_name = 'leave/leave_calendar_ultra_modern.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .holiday_service import holiday_service
        from .leave_balance_service import leave_balance_service
        
        # Paramètres du calendrier
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        employee = self.request.GET.get('employee')
        
        # Générer le calendrier
        try:
            calendar_data = holiday_service.get_leave_calendar(year, month)
        except Exception as e:
            # En cas d'erreur, afficher un calendrier vide
            calendar_data = {
                'calendar': [],
                'holidays_list': [],
            }
            context['error'] = str(e)
            return context
        
        context.update({
            'current_year': year,
            'current_month': month,
            'current_month_name': timezone.datetime(year, month, 1).strftime('%B'),
            'calendar_days': calendar_data['calendar'],
            'holidays_list': calendar_data['holidays_list'],
            'total_holidays': len(calendar_data['holidays_list']),
            'total_leaves': sum(1 for day in calendar_data['calendar'] if day['leaves']),
            'working_days': sum(1 for day in calendar_data['calendar'] if not day['is_weekend'] and not day['is_holiday']),
            'remaining_days': leave_balance_service.get_remaining_balance(self.request.user),
            'available_years': range(2020, timezone.now().year + 2),
            'months': {i: timezone.datetime(year, i, 1).strftime('%B') for i in range(1, 13)},
            'employees': User.objects.filter(leave_requests__isnull=False).distinct(),
            'today': timezone.now().date(),
        })
        
        return context