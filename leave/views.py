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


class LeaveApprovalListView(EnhancedLoginRequiredMixin, ListView):
    """Vue pour lister les demandes à approuver."""
    model = LeaveRequest
    template_name = 'leave/leave_approval_list.html'
    context_object_name = 'leave_requests'


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