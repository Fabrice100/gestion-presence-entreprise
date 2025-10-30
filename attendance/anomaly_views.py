"""
Vues pour la résolution des anomalies de pointage.

Conforme aux spécifications: MODULE 1 - Rapport d'Anomalies
- Manager: peut justifier/résoudre anomalies de son équipe
- RH: peut résoudre toutes les anomalies
- Workflow: pending → justified/resolved/ignored
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta

"""Vues des anomalies désactivées: toutes redirections."""
from accounts.models import EmployeeProfile
from common.mixins import ManagerRequiredMixin


class ManagerAnomalyListView(ManagerRequiredMixin, ListView):
    """
    Accès supprimé pour les managers: redirection vers le dashboard manager.
    La gestion des anomalies est réservée au RH.
    """
    def dispatch(self, request, *args, **kwargs):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.info(request, "La gestion des anomalies est réservée au RH.")
        return redirect('dashboard:manager_dashboard')


class AnomalyResolutionView(LoginRequiredMixin, View):
    """
    Vue pour résoudre une anomalie (Manager ou RH).
    
    Actions possibles:
    - Justifier (justified) : Anomalie expliquée par employé
    - Résoudre (resolved) : Anomalie corrigée
    - Ignorer (ignored) : Anomalie sans importance
    """
    
    def post(self, request, pk):
        """Traite la résolution d'une anomalie."""
        messages.info(request, "La fonctionnalité anomalies est désactivée.")
        return redirect('reports:reports_dashboard')


class RHAnomalyListView(LoginRequiredMixin, ListView):
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "La fonctionnalité anomalies est désactivée.")
        return redirect('reports:reports_dashboard')


class AnomalyDetailView(LoginRequiredMixin, View):
    """
    Vue détaillée d'une anomalie avec formulaire de résolution.
    """
    
    def get(self, request, pk):
        """Affiche les détails de l'anomalie."""
        messages.info(request, "La fonctionnalité anomalies est désactivée.")
        return redirect('reports:reports_dashboard')
