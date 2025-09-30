"""
Vues pour l'application reports (rapports et paramètres).

Ce module contient les vues pour :
- Génération de rapports
- Gestion des paramètres système
- Modèles de rapports

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView
from django.contrib import messages


class LoginRequiredMixin:
    """Mixin pour exiger une authentification."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Vous devez être connecté pour accéder à cette page.')
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)


class ReportListView(LoginRequiredMixin, TemplateView):
    """Vue pour lister les rapports disponibles."""
    template_name = 'reports/report_list.html'


class AttendanceReportView(LoginRequiredMixin, TemplateView):
    """Vue pour les rapports de présence."""
    template_name = 'reports/attendance_report.html'


class LeaveReportView(LoginRequiredMixin, TemplateView):
    """Vue pour les rapports de congés."""
    template_name = 'reports/leave_report.html'


class SummaryReportView(LoginRequiredMixin, TemplateView):
    """Vue pour les rapports récapitulatifs."""
    template_name = 'reports/summary_report.html'


class SystemSettingsView(LoginRequiredMixin, TemplateView):
    """Vue pour les paramètres système."""
    template_name = 'reports/system_settings.html'


class ReportTemplateListView(LoginRequiredMixin, ListView):
    """Vue pour lister les modèles de rapports."""
    template_name = 'reports/report_template_list.html'


# Vues temporaires pour éviter les erreurs 404
class ReportGenerateView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/placeholder.html'


class ReportDownloadView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/placeholder.html'


class SystemSettingEditView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/placeholder.html'


class ReportTemplateDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/placeholder.html'


class ReportTemplateCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/placeholder.html'