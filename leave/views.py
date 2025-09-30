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

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.contrib import messages

from .models import LeaveRequest, LeaveBalance, LeaveType, Holiday


class LoginRequiredMixin:
    """Mixin pour exiger une authentification."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Vous devez être connecté pour accéder à cette page.')
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)


class LeaveRequestListView(LoginRequiredMixin, ListView):
    """Vue pour lister les demandes de congés."""
    model = LeaveRequest
    template_name = 'leave/leave_request_list.html'
    context_object_name = 'leave_requests'
    
    def get_queryset(self):
        return LeaveRequest.objects.filter(employee=self.request.user)


class LeaveRequestCreateView(LoginRequiredMixin, TemplateView):
    """Vue pour créer une demande de congé."""
    template_name = 'leave/leave_request_create.html'


class LeaveBalanceListView(LoginRequiredMixin, ListView):
    """Vue pour lister les soldes de congés."""
    model = LeaveBalance
    template_name = 'leave/leave_balance_list.html'
    context_object_name = 'leave_balances'
    
    def get_queryset(self):
        return LeaveBalance.objects.filter(employee=self.request.user)


class LeaveApprovalListView(LoginRequiredMixin, ListView):
    """Vue pour lister les demandes à approuver."""
    model = LeaveRequest
    template_name = 'leave/leave_approval_list.html'
    context_object_name = 'leave_requests'


class LeaveTypeListView(LoginRequiredMixin, ListView):
    """Vue pour lister les types de congés."""
    model = LeaveType
    template_name = 'leave/leave_type_list.html'
    context_object_name = 'leave_types'


class HolidayListView(LoginRequiredMixin, ListView):
    """Vue pour lister les jours fériés."""
    model = Holiday
    template_name = 'leave/holiday_list.html'
    context_object_name = 'holidays'


# Vues temporaires pour éviter les erreurs 404
class LeaveRequestDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveRequestEditView(LoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveRequestCancelView(LoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveApprovalView(LoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveRejectionView(LoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveBalanceDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveTypeDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class HolidayDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveReportView(LoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'


class LeaveCalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'leave/placeholder.html'