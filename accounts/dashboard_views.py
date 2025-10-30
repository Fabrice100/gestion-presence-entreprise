"""
Vues pour les tableaux de bord par rôle.

Ce module contient les vues pour les différents tableaux de bord :
- Dashboard général (redirection selon le rôle)
- Dashboard employé
- Dashboard manager
- Dashboard RH
- Dashboard administrateur

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date, timedelta, datetime

from accounts.models import EmployeeProfile, Department
from attendance.models import Attendance
from leave.models import LeaveRequest, LeaveBalance

# Import du mixin centralisé (principe DRY)
from common.mixins import (
    EnhancedLoginRequiredMixin, 
    EmployeeRequiredMixin, 
    ManagerRequiredMixin, 
    RHRequiredMixin,
    AdminRequiredMixin
)


class DashboardView(EnhancedLoginRequiredMixin, TemplateView):
    """
    Vue principale du tableau de bord qui redirige selon le rôle de l'utilisateur.
    """
    
    def get(self, request, *args, **kwargs):
        """Redirige vers le tableau de bord approprié selon le rôle."""
        try:
            profile = request.user.employee_profile
        except EmployeeProfile.DoesNotExist:
            # Si pas de profil, rediriger vers la création de profil
            return redirect('accounts:profile_edit')
        
        # Redirection selon le rôle métier
        # Note: Les superusers (admins techniques) sont gérés par le middleware
        if profile.is_rh():
            return redirect('dashboard:rh_dashboard')
        elif profile.is_manager():
            return redirect('dashboard:manager_dashboard')
        else:
            return redirect('dashboard:employee_dashboard')


class EmployeeDashboardView(EmployeeRequiredMixin, TemplateView):
    """
    Tableau de bord pour les employés.
    Affiche les informations de présence et congés personnelles.
    """
    template_name = 'dashboard/employee_dashboard_ultra_modern.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        
        # Pointage du jour
        today_attendance = Attendance.objects.filter(
            employee=user,
            date=today
        ).order_by('time')
        
        # Dernières présences
        recent_attendance = Attendance.objects.filter(
            employee=user
        ).order_by('-date', '-time')[:10]
        
        # Demandes de congés récentes
        recent_leave_requests = LeaveRequest.objects.filter(
            employee=user
        ).order_by('-created_at')[:5]
        
        # Soldes de congés - Initialiser si nécessaire
        from leave.leave_balance_service import leave_balance_service
        
        # S'assurer que les soldes sont initialisés pour l'année courante
        leave_balance_service.initialize_employee_balance(user, today.year)
        
        leave_balances = LeaveBalance.objects.filter(
            employee=user,
            year=today.year
        ).select_related('leave_type')
        
        # Statistiques du mois
        month_start = today.replace(day=1)
        month_attendance = Attendance.objects.filter(
            employee=user,
            date__gte=month_start,
            date__lte=today
        )
        
        # Calcul des statistiques
        total_work_days = month_attendance.filter(punch_type='in').count()
        total_hours = 0
        today_hours = 0
        
        # Calcul des heures du mois
        for attendance in month_attendance.filter(punch_type='out'):
            duration = attendance.get_duration_with_previous()
            if duration:
                total_hours += duration
        
        # Calcul des heures d'aujourd'hui
        for attendance in today_attendance.filter(punch_type='out'):
            duration = attendance.get_duration_with_previous()
            if duration:
                today_hours += duration
        
        # Anomalies désactivées → pas de compteur
        
        # Solde total de congés (somme de tous les types)
        total_leave_balance = sum([lb.remaining_balance for lb in leave_balances])
        
        # Statut actuel (dernier pointage)
        last_punch = today_attendance.last() if today_attendance.exists() else None
        current_status = 'present' if last_punch and last_punch.punch_type == 'in' else 'absent'
        # Utiliser time au lieu de timestamp (qui n'existe pas dans le modèle)
        last_punch_time = None
        if last_punch:
            last_punch_time = datetime.combine(last_punch.date, last_punch.time)
        
        # Pointages d'aujourd'hui pour la timeline
        today_punches = today_attendance.all()
        
        # Calcul des heures par jour pour le graphique hebdomadaire
        from datetime import timedelta
        week_start = today - timedelta(days=today.weekday())  # Lundi de cette semaine
        week_hours = []
        week_labels = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_attendance = Attendance.objects.filter(
                employee=user,
                date=day,
                punch_type='out'
            )
            
            day_total = 0
            for att in day_attendance:
                duration = att.get_duration_with_previous()
                if duration:
                    day_total += duration
            
            week_hours.append(round(day_total, 1))
        
        context.update({
            'today_attendance': today_attendance,
            'recent_attendance': recent_attendance,
            'recent_leave_requests': recent_leave_requests,
            'leave_balances': leave_balances,
            'total_work_days': total_work_days,
            'month_hours': round(total_hours, 1),
            'today_hours': round(today_hours, 1),
            # 'pending_anomalies': 0,
            'leave_balance': total_leave_balance,
            'current_status': current_status,
            'last_punch_time': last_punch_time,
            'today_punches': today_punches,
            'today': today,
            'week_hours': week_hours,  # Nouvelles données pour le graphique
            'week_labels': week_labels,
        })
        
        return context


class ManagerDashboardView(ManagerRequiredMixin, TemplateView):
    """
    Tableau de bord pour les managers.
    """
    template_name = 'dashboard/manager_dashboard_ultra_modern.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        
        # FILTRAGE STRICT PAR DÉPARTEMENT (conforme aux spécifications)
        # Le Manager voit SEULEMENT son département/service
        manager_profile = user.employee_profile
        manager_department = manager_profile.department
        
        if not manager_department:
            # Manager sans département : aucun employé géré
            managed_profiles = EmployeeProfile.objects.none()
        else:
            # Filtrer STRICTEMENT par département (exclure le Manager lui-même)
            managed_profiles = EmployeeProfile.objects.filter(
                department=manager_department,
                is_active=True
            ).exclude(user=user)  # Exclure le Manager des stats
        
        # Obtenir les utilisateurs des employés gérés
        managed_users = [profile.user for profile in managed_profiles]
        
        # Présences de l'équipe aujourd'hui
        team_attendance_today = Attendance.objects.filter(
            employee__in=managed_users,
            date=today
        ).select_related('employee')
        
        # Demandes de congés en attente
        pending_leave_requests = LeaveRequest.objects.filter(
            employee__in=managed_users,
            status='pending'
        ).select_related('employee', 'leave_type')
        
        # Anomalies désactivées
        
        # Statistiques de l'équipe
        team_stats = {
            'total_employees': managed_profiles.count(),
            'present_today': team_attendance_today.filter(punch_type='in').count(),
            'pending_requests': pending_leave_requests.count(),
            # 'pending_anomalies': 0,
        }
        
        # Graphique des présences de la semaine
        week_start = today - timedelta(days=today.weekday())
        week_attendance = Attendance.objects.filter(
            employee__in=managed_users,
            date__gte=week_start,
            date__lte=today
        ).values('date').annotate(
            total_punches=Count('id')
        ).order_by('date')
        
        context.update({
            'managed_employees': managed_profiles,
            'team_attendance_today': team_attendance_today,
            'pending_leave_requests': pending_leave_requests,
            # 'team_anomalies': [],
            'team_stats': team_stats,
            'week_attendance': week_attendance,
            'today': today,
        })
        
        return context


class RhDgDashboardView(RHRequiredMixin, TemplateView):
    """
    Tableau de bord pour les RH et DG.
    """
    template_name = 'dashboard/rh_dg_dashboard_ultra_modern.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        
        # Tous les employés actifs (exclure RH des statistiques employés)
        all_employees = EmployeeProfile.objects.filter(is_active=True).exclude(role='rh')
        
        # Présences globales aujourd'hui
        global_attendance_today = Attendance.objects.filter(
            date=today
        ).select_related('employee__employee_profile')
        
        # Demandes de congés en attente de validation RH
        pending_rh_requests = LeaveRequest.objects.filter(
            status='approved_manager'
        ).select_related('employee__employee_profile', 'leave_type', 'manager')
        
        # Anomalies désactivées
        
        # Statistiques globales
        global_stats = {
            'total_employees': all_employees.count(),
            'present_today': global_attendance_today.filter(punch_type='in').count(),
            'pending_rh_requests': pending_rh_requests.count(),
            # 'pending_anomalies': 0,
        }
        
        # Statistiques par département
        department_stats = []
        # RH peut gérer tous les départements
        all_departments = Department.objects.filter(is_active=True)
        for dept in all_departments:
            dept_employees = all_employees.filter(department=dept)
            dept_present = global_attendance_today.filter(
                employee__employee_profile__department=dept,
                punch_type='in'
            ).count()
            
            department_stats.append({
                'department': dept,
                'total_employees': dept_employees.count(),
                'present_today': dept_present,
                'attendance_rate': round(
                    (dept_present / dept_employees.count() * 100) 
                    if dept_employees.count() > 0 else 0, 1
                )
            })
        
        # Graphique des présences mensuelles
        month_start = today.replace(day=1)
        monthly_attendance = Attendance.objects.filter(
            date__gte=month_start,
            date__lte=today
        ).values('date').annotate(
            total_punches=Count('id')
        ).order_by('date')
        
        context.update({
            'all_employees': all_employees,
            'global_attendance_today': global_attendance_today,
            'pending_rh_requests': pending_rh_requests,
            # 'global_anomalies': [],
            'global_stats': global_stats,
            'department_stats': department_stats,
            'monthly_attendance': monthly_attendance,
            'today': today,
            # Variables pour le template
            'total_employees': global_stats['total_employees'],
            'total_departments': len(department_stats),
            'pending_validations': global_stats['pending_rh_requests'],
            'total_leave_requests': global_stats['pending_rh_requests'],
            'recent_employees': all_employees[:5],  # ✅ Ajout de la variable manquante
        })
        
        return context



