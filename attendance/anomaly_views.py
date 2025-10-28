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

from attendance.models import AttendanceAnomaly, Attendance
from accounts.models import EmployeeProfile
from common.mixins import ManagerRequiredMixin


class ManagerAnomalyListView(ManagerRequiredMixin, ListView):
    """
    Vue pour lister les anomalies de l'équipe du Manager.
    
    Filtrage strict par département (conforme Task 3).
    """
    model = AttendanceAnomaly
    template_name = 'attendance/manager_anomaly_list.html'
    context_object_name = 'anomalies'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtre les anomalies du département du Manager uniquement."""
        # FILTRAGE STRICT PAR DÉPARTEMENT
        manager_profile = self.request.user.employee_profile
        manager_department = manager_profile.department
        
        if not manager_department:
            return AttendanceAnomaly.objects.none()
        
        # Seulement anomalies du département
        queryset = AttendanceAnomaly.objects.filter(
            attendance__employee__employee_profile__department=manager_department
        ).select_related(
            'attendance__employee',
            'attendance__employee__employee_profile',
            'resolved_by'
        ).order_by('-created_at')
        
        # Filtres
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        anomaly_type = self.request.GET.get('type')
        if anomaly_type:
            queryset = queryset.filter(anomaly_type=anomaly_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajoute les statistiques."""
        context = super().get_context_data(**kwargs)
        
        # Récupérer département Manager
        manager_department = self.request.user.employee_profile.department
        
        if manager_department:
            all_anomalies = AttendanceAnomaly.objects.filter(
                attendance__employee__employee_profile__department=manager_department
            )
        else:
            all_anomalies = AttendanceAnomaly.objects.none()
        
        # Statistiques
        context['stats'] = {
            'pending': all_anomalies.filter(status='pending').count(),
            'justified': all_anomalies.filter(status='justified').count(),
            'resolved': all_anomalies.filter(status='resolved').count(),
            'total': all_anomalies.count()
        }
        
        # Types pour filtre
        context['anomaly_types'] = AttendanceAnomaly.ANOMALY_TYPE_CHOICES
        context['status_choices'] = AttendanceAnomaly.STATUS_CHOICES
        
        return context


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
        anomaly = get_object_or_404(AttendanceAnomaly, pk=pk)
        
        # Vérifier les permissions
        user_profile = request.user.employee_profile
        employee_department = anomaly.attendance.employee.employee_profile.department
        
        # Manager : seulement son département
        if user_profile.role == 'manager':
            if user_profile.department != employee_department:
                messages.error(request, "❌ Vous ne pouvez résoudre que les anomalies de votre département.")
                return redirect('attendance:manager_anomaly_list')
        
        # RH uniquement pour vue globale
        elif user_profile.role != 'rh':
            messages.error(request, "❌ Vous n'avez pas les permissions pour résoudre cette anomalie.")
            return redirect('dashboard:employee_dashboard')
        
        # Récupérer les données
        action = request.POST.get('action')  # 'justified', 'resolved', 'ignored'
        justification = request.POST.get('justification', '').strip()
        
        # Validation
        if action not in ['justified', 'resolved', 'ignored']:
            messages.error(request, "❌ Action invalide.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        if not justification:
            messages.error(request, "❌ La justification est obligatoire.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Mettre à jour l'anomalie
        anomaly.status = action
        anomaly.justification = justification
        anomaly.resolved_by = request.user
        anomaly.resolved_at = timezone.now()
        anomaly.save()
        
        # Message de succès
        action_messages = {
            'justified': '✅ Anomalie justifiée avec succès.',
            'resolved': '✅ Anomalie résolue avec succès.',
            'ignored': '✅ Anomalie ignorée.'
        }
        messages.success(request, action_messages[action])
        
        # Redirection
        if user_profile.role == 'manager':
            return redirect('attendance:manager_anomaly_list')
        else:
            return redirect('attendance:rh_anomaly_list')


class RHAnomalyListView(LoginRequiredMixin, ListView):
    """
    Vue pour lister TOUTES les anomalies (RH).
    
    Vue globale entreprise, tous départements.
    """
    model = AttendanceAnomaly
    template_name = 'attendance/rh_anomaly_list.html'
    context_object_name = 'anomalies'
    paginate_by = 30
    
    def get_queryset(self):
        """Toutes les anomalies (RH voit tout)."""
        # Vérifier rôle RH uniquement
        if self.request.user.employee_profile.role != 'rh':
            return AttendanceAnomaly.objects.none()
        
        queryset = AttendanceAnomaly.objects.all().select_related(
            'attendance__employee',
            'attendance__employee__employee_profile__department',
            'resolved_by'
        ).order_by('-created_at')
        
        # Filtres
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        anomaly_type = self.request.GET.get('type')
        if anomaly_type:
            queryset = queryset.filter(anomaly_type=anomaly_type)
        
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(
                attendance__employee__employee_profile__department__name=department
            )
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(attendance__employee__first_name__icontains=search) |
                Q(attendance__employee__last_name__icontains=search) |
                Q(attendance__employee__employee_profile__employee_id__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajoute les statistiques globales."""
        context = super().get_context_data(**kwargs)
        
        all_anomalies = AttendanceAnomaly.objects.all()
        
        # Statistiques globales
        context['stats'] = {
            'pending': all_anomalies.filter(status='pending').count(),
            'justified': all_anomalies.filter(status='justified').count(),
            'resolved': all_anomalies.filter(status='resolved').count(),
            'ignored': all_anomalies.filter(status='ignored').count(),
            'total': all_anomalies.count()
        }
        
        # Départements pour filtre
        from accounts.models import Department
        context['departments'] = Department.objects.filter(is_active=True)
        context['anomaly_types'] = AttendanceAnomaly.ANOMALY_TYPE_CHOICES
        context['status_choices'] = AttendanceAnomaly.STATUS_CHOICES
        
        return context


class AnomalyDetailView(LoginRequiredMixin, View):
    """
    Vue détaillée d'une anomalie avec formulaire de résolution.
    """
    
    def get(self, request, pk):
        """Affiche les détails de l'anomalie."""
        anomaly = get_object_or_404(
            AttendanceAnomaly.objects.select_related(
                'attendance__employee',
                'attendance__employee__employee_profile',
                'resolved_by'
            ),
            pk=pk
        )
        
        # Vérifier permissions
        user_profile = request.user.employee_profile
        employee_department = anomaly.attendance.employee.employee_profile.department
        
        # Manager : seulement son département
        if user_profile.role == 'manager':
            if user_profile.department != employee_department:
                messages.error(request, "❌ Accès refusé.")
                return redirect('attendance:manager_anomaly_list')
        
        # Employé : seulement ses propres anomalies
        elif user_profile.role == 'employee':
            if anomaly.attendance.employee != request.user:
                messages.error(request, "❌ Accès refusé.")
                return redirect('dashboard:employee_dashboard')
        
        context = {
            'anomaly': anomaly,
            'attendance': anomaly.attendance,
            'can_resolve': user_profile.role in ['manager', 'rh'] and anomaly.status == 'pending'
        }
        
        return render(request, 'attendance/anomaly_detail.html', context)
