"""
Personnalisation de l'interface Django Admin.

Améliore l'interface admin avec:
- Dashboard avec statistiques
- Personnalisation du titre et des couleurs
- Raccourcis vers les fonctionnalités principales
"""

from django.contrib import admin
from django.db.models import Count, Q, Avg
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta


class CustomAdminSite(admin.AdminSite):
    """Site d'administration personnalisé."""
    
    site_header = "🏢 Gestion de Présence - Administration"
    site_title = "Admin Présence"
    index_title = "📊 Tableau de bord administrateur"
    
    def index(self, request, extra_context=None):
        """Page d'accueil personnalisée avec statistiques."""
        extra_context = extra_context or {}
        
        # Import ici pour éviter les imports circulaires
        from django.contrib.auth.models import User
        from accounts.models import EmployeeProfile, Department
        from attendance.models import Attendance
        from leave.models import LeaveRequest
        
        today = date.today()
        
        # === STATISTIQUES EMPLOYÉS ===
        total_employees = EmployeeProfile.objects.count()
        active_employees = EmployeeProfile.objects.filter(is_active=True).count()
        can_punch_employees = EmployeeProfile.objects.filter(can_punch=True).count()
        
        employees_by_role = EmployeeProfile.objects.values('role').annotate(
            count=Count('id')
        ).order_by('role')
        
        # === STATISTIQUES POINTAGES AUJOURD'HUI ===
        today_attendances = Attendance.objects.filter(date=today)
        total_punches_today = today_attendances.count()
        arrivals_today = today_attendances.filter(punch_type='in').count()
        departures_today = today_attendances.filter(punch_type='out').count()
        late_today = today_attendances.filter(status='late').count()
        
        # Taux de présence aujourd'hui
        if can_punch_employees > 0:
            presence_rate = round((arrivals_today / can_punch_employees) * 100, 1)
        else:
            presence_rate = 0
        
        # === STATISTIQUES POINTAGES CE MOIS ===
        first_day_month = today.replace(day=1)
        month_attendances = Attendance.objects.filter(
            date__gte=first_day_month,
            date__lte=today
        )
        total_punches_month = month_attendances.count()
        late_month = month_attendances.filter(status='late').count()
        
        # Distance GPS moyenne
        avg_distance = month_attendances.filter(
            distance_from_site__isnull=False
        ).aggregate(Avg('distance_from_site'))['distance_from_site__avg']
        
        # === STATISTIQUES CONGÉS ===
        pending_leaves = LeaveRequest.objects.filter(status='pending').count()
        approved_manager_leaves = LeaveRequest.objects.filter(
            status='approved_manager'
        ).count()
        on_leave_today = LeaveRequest.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            status='approved_rh'
        ).count()
        
        # === STATISTIQUES DÉPARTEMENTS ===
        total_departments = Department.objects.filter(is_active=True).count()
        departments_stats = Department.objects.filter(is_active=True).annotate(
            employee_count=Count('employees')
        ).order_by('-employee_count')[:5]
        
        # === ALERTES ===
        alerts = []
        
        # Alerte: Beaucoup de retards aujourd'hui
        if late_today > 5:
            alerts.append({
                'level': 'warning',
                'icon': '⚠️',
                'message': f'{late_today} retards détectés aujourd\'hui'
            })
        
        # Alerte: Demandes de congés en attente
        total_pending = pending_leaves + approved_manager_leaves
        if total_pending > 0:
            alerts.append({
                'level': 'info',
                'icon': 'ℹ️',
                'message': f'{total_pending} demande(s) de congés à valider'
            })
        
        # Alerte: Taux de présence faible
        if presence_rate < 80 and can_punch_employees > 0:
            alerts.append({
                'level': 'warning',
                'icon': '⚠️',
                'message': f'Taux de présence faible: {presence_rate}%'
            })
        
        # === RACCOURCIS ===
        shortcuts = [
            {
                'title': 'Créer un employé',
                'url': reverse('admin:accounts_employeeprofile_add'),
                'icon': '👤',
                'color': '#4CAF50'
            },
            {
                'title': 'Voir pointages aujourd\'hui',
                'url': reverse('admin:attendance_attendance_changelist') + f'?date__exact={today}',
                'icon': '📍',
                'color': '#2196F3'
            },
            {
                'title': 'Demandes de congés',
                'url': reverse('admin:leave_leaverequest_changelist') + '?status__in=pending,approved_manager',
                'icon': '📅',
                'color': '#FF9800'
            },
            {
                'title': 'Configuration GPS',
                'url': reverse('admin:attendance_companysettings_changelist'),
                'icon': '🌍',
                'color': '#9C27B0'
            },
        ]
        
        # Ajouter au contexte
        extra_context['dashboard_stats'] = {
            'employees': {
                'total': total_employees,
                'active': active_employees,
                'can_punch': can_punch_employees,
                'by_role': list(employees_by_role)
            },
            'today': {
                'total_punches': total_punches_today,
                'arrivals': arrivals_today,
                'departures': departures_today,
                'late': late_today,
                'presence_rate': presence_rate,
                'on_leave': on_leave_today
            },
            'month': {
                'total_punches': total_punches_month,
                'late': late_month,
                'avg_distance': round(avg_distance, 1) if avg_distance else 0
            },
            'leaves': {
                'pending': pending_leaves,
                'approved_manager': approved_manager_leaves,
                'on_leave_today': on_leave_today
            },
            'departments': {
                'total': total_departments,
                'top': list(departments_stats)
            }
        }
        extra_context['alerts'] = alerts
        extra_context['shortcuts'] = shortcuts
        extra_context['today'] = today
        
        return super().index(request, extra_context)


# Créer une instance du site personnalisé
admin_site = CustomAdminSite(name='custom_admin')
