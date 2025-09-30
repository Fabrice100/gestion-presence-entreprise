"""
Vues pour les tableaux de bord par rôle.

Ce module contient les vues pour les différents tableaux de bord :
- Dashboard général (redirection selon le rôle)
- Dashboard employé
- Dashboard manager
- Dashboard RH/DG
- Dashboard administrateur

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date, timedelta

from accounts.models import EmployeeProfile
from attendance.models import Attendance, AttendanceAnomaly
from leave.models import LeaveRequest, LeaveBalance


class LoginRequiredMixin:
    """Mixin pour exiger une authentification."""
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
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
        
        # Redirection selon le rôle
        if profile.is_admin():
            return redirect('dashboard:admin_dashboard')
        elif profile.is_rh_dg():
            return redirect('dashboard:rh_dg_dashboard')
        elif profile.is_manager():
            return redirect('dashboard:manager_dashboard')
        else:
            return redirect('dashboard:employee_dashboard')


class EmployeeDashboardView(LoginRequiredMixin, TemplateView):
    """
    Tableau de bord pour les employés.
    """
    template_name = 'dashboard/employee_dashboard.html'
    
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
        
        # Soldes de congés
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
        for attendance in month_attendance.filter(punch_type='out'):
            duration = attendance.get_duration_with_previous()
            if duration:
                total_hours += duration
        
        # Anomalies en attente
        pending_anomalies = AttendanceAnomaly.objects.filter(
            attendance__employee=user,
            status='pending'
        ).count()
        
        context.update({
            'today_attendance': today_attendance,
            'recent_attendance': recent_attendance,
            'recent_leave_requests': recent_leave_requests,
            'leave_balances': leave_balances,
            'total_work_days': total_work_days,
            'total_hours': round(total_hours, 1),
            'pending_anomalies': pending_anomalies,
            'today': today,
        })
        
        return context


class ManagerDashboardView(LoginRequiredMixin, TemplateView):
    """
    Tableau de bord pour les managers.
    """
    template_name = 'dashboard/manager_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        
        # Employés gérés
        managed_employees = user.managed_employees.filter(
            employee_profile__is_active=True
        )
        
        # Présences de l'équipe aujourd'hui
        team_attendance_today = Attendance.objects.filter(
            employee__in=managed_employees,
            date=today
        ).select_related('employee__employee_profile')
        
        # Demandes de congés en attente
        pending_leave_requests = LeaveRequest.objects.filter(
            employee__in=managed_employees,
            status='pending'
        ).select_related('employee__employee_profile', 'leave_type')
        
        # Anomalies de l'équipe
        team_anomalies = AttendanceAnomaly.objects.filter(
            attendance__employee__in=managed_employees,
            status='pending'
        ).select_related('attendance__employee__employee_profile')
        
        # Statistiques de l'équipe
        team_stats = {
            'total_employees': managed_employees.count(),
            'present_today': team_attendance_today.filter(punch_type='in').count(),
            'pending_requests': pending_leave_requests.count(),
            'pending_anomalies': team_anomalies.count(),
        }
        
        # Graphique des présences de la semaine
        week_start = today - timedelta(days=today.weekday())
        week_attendance = Attendance.objects.filter(
            employee__in=managed_employees,
            date__gte=week_start,
            date__lte=today
        ).values('date').annotate(
            total_punches=Count('id')
        ).order_by('date')
        
        context.update({
            'managed_employees': managed_employees,
            'team_attendance_today': team_attendance_today,
            'pending_leave_requests': pending_leave_requests,
            'team_anomalies': team_anomalies,
            'team_stats': team_stats,
            'week_attendance': week_attendance,
            'today': today,
        })
        
        return context


class RHDGDashboardView(LoginRequiredMixin, TemplateView):
    """
    Tableau de bord pour les RH/DG.
    """
    template_name = 'dashboard/rh_dg_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        
        # Tous les employés actifs
        all_employees = EmployeeProfile.objects.filter(is_active=True)
        
        # Présences globales aujourd'hui
        global_attendance_today = Attendance.objects.filter(
            date=today
        ).select_related('employee__employee_profile')
        
        # Demandes de congés en attente de validation RH
        pending_rh_requests = LeaveRequest.objects.filter(
            status='approved_manager'
        ).select_related('employee__employee_profile', 'leave_type', 'manager')
        
        # Anomalies globales
        global_anomalies = AttendanceAnomaly.objects.filter(
            status='pending'
        ).select_related('attendance__employee__employee_profile')
        
        # Statistiques globales
        global_stats = {
            'total_employees': all_employees.count(),
            'present_today': global_attendance_today.filter(punch_type='in').count(),
            'pending_rh_requests': pending_rh_requests.count(),
            'pending_anomalies': global_anomalies.count(),
        }
        
        # Statistiques par département
        department_stats = []
        for dept in user.managed_departments.all():
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
            'global_anomalies': global_anomalies,
            'global_stats': global_stats,
            'department_stats': department_stats,
            'monthly_attendance': monthly_attendance,
            'today': today,
        })
        
        return context


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    """
    Tableau de bord pour les administrateurs.
    """
    template_name = 'dashboard/admin_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        
        # Statistiques globales
        total_users = EmployeeProfile.objects.count()
        active_users = EmployeeProfile.objects.filter(is_active=True).count()
        total_departments = EmployeeProfile.objects.values('department').distinct().count()
        
        # Présences aujourd'hui
        today_attendance = Attendance.objects.filter(date=today)
        today_present = today_attendance.filter(punch_type='in').count()
        
        # Anomalies globales
        total_anomalies = AttendanceAnomaly.objects.count()
        pending_anomalies = AttendanceAnomaly.objects.filter(status='pending').count()
        
        # Demandes de congés
        total_leave_requests = LeaveRequest.objects.count()
        pending_leave_requests = LeaveRequest.objects.filter(
            status__in=['pending', 'approved_manager']
        ).count()
        
        # Statistiques système
        system_stats = {
            'total_users': total_users,
            'active_users': active_users,
            'total_departments': total_departments,
            'today_present': today_present,
            'total_anomalies': total_anomalies,
            'pending_anomalies': pending_anomalies,
            'total_leave_requests': total_leave_requests,
            'pending_leave_requests': pending_leave_requests,
        }
        
        # Activité récente
        recent_activities = []
        
        # Derniers pointages
        recent_punches = Attendance.objects.order_by('-created_at')[:10]
        for punch in recent_punches:
            recent_activities.append({
                'type': 'punch',
                'description': f"{punch.employee.get_full_name()} a pointé {punch.get_punch_type_display()}",
                'time': punch.created_at,
                'user': punch.employee,
            })
        
        # Dernières demandes de congés
        recent_requests = LeaveRequest.objects.order_by('-created_at')[:5]
        for request in recent_requests:
            recent_activities.append({
                'type': 'leave_request',
                'description': f"{request.employee.get_full_name()} a demandé des congés",
                'time': request.created_at,
                'user': request.employee,
            })
        
        # Trier par date
        recent_activities.sort(key=lambda x: x['time'], reverse=True)
        recent_activities = recent_activities[:10]
        
        context.update({
            'system_stats': system_stats,
            'recent_activities': recent_activities,
            'today': today,
        })
        
        return context

