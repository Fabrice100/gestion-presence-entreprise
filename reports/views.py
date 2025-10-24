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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView
from django.contrib import messages

# Import du mixin centralisé (principe DRY)
from common.mixins import EnhancedLoginRequiredMixin, ManagerRequiredMixin


class ReportListView(ManagerRequiredMixin, TemplateView):
    """Vue pour lister les rapports disponibles."""
    template_name = 'reports/report_list.html'


class AttendanceReportView(ManagerRequiredMixin, TemplateView):
    """Vue pour les rapports de présence."""
    template_name = 'reports/attendance_report.html'


class LeaveReportView(ManagerRequiredMixin, TemplateView):
    """Vue pour les rapports de congés."""
    template_name = 'reports/leave_report.html'


class SummaryReportView(ManagerRequiredMixin, TemplateView):
    """Vue pour les rapports récapitulatifs."""
    template_name = 'reports/summary_report.html'


class SystemSettingsView(ManagerRequiredMixin, TemplateView):
    """Vue pour les paramètres système."""
    template_name = 'reports/system_settings.html'


class ReportTemplateListView(ManagerRequiredMixin, ListView):
    """Vue pour lister les modèles de rapports."""
    template_name = 'reports/report_template_list.html'


