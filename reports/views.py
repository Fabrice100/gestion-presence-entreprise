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


# Note: Les vues de rapports sont dans report_views.py
# ReportListView, AttendanceReportView, LeaveReportView, SummaryReportView
# ont été déplacées ou supprimées car non utilisées


class SystemSettingsView(ManagerRequiredMixin, TemplateView):
    """Vue pour les paramètres système."""
    template_name = 'reports/system_settings.html'


class ReportTemplateListView(ManagerRequiredMixin, ListView):
    """Vue pour lister les modèles de rapports."""
    template_name = 'reports/report_template_list.html'


