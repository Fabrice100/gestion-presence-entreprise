"""
Vues pour la génération de rapports avancés.

Ce module contient les vues pour :
- Rapports de présence détaillés
- Rapports de congés avec statistiques
- Rapports d'anomalies
- Export PDF/Excel
- Graphiques et visualisations

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, TemplateView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from django.contrib.auth.models import User
from datetime import date, timedelta, datetime
from calendar import monthrange
import json

from .models import SystemSettings, ReportTemplate
from accounts.models import EmployeeProfile, Department
from attendance.models import Attendance, AttendanceAnomaly
from leave.models import LeaveRequest, LeaveBalance, LeaveType


class ReportsDashboardView(LoginRequiredMixin, TemplateView):
    """
    Tableau de bord des rapports avec statistiques globales.
    """
    template_name = 'reports/reports_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = user.employee_profile
        today = date.today()
        
        # Statistiques globales
        context.update(self._get_global_stats(today, profile))
        
        # Graphiques des données
        context.update(self._get_charts_data(today, profile))
        
        # Rapports récents
        context['recent_reports'] = self._get_recent_reports()
        
        return context
    
    def _get_global_stats(self, today, profile):
        """Calcule les statistiques globales."""
        stats = {}
        
        if profile.role == 'rh':
            # Statistiques pour RH (toute l'entreprise)
            stats.update({
                'total_employees': EmployeeProfile.objects.filter(is_active=True).exclude(role='rh').count(),
                'total_departments': Department.objects.count(),
                'present_today': self._get_present_today_count(),
                'absent_today': self._get_absent_today_count(),
                'on_leave_today': self._get_on_leave_today_count(),
                'pending_leave_requests': LeaveRequest.objects.filter(status='pending').count(),
                'anomalies_pending': AttendanceAnomaly.objects.filter(status='pending').count(),
            })
        elif profile.role == 'manager':
            # Statistiques pour manager (son équipe)
            managed_employees = User.objects.filter(employee_profile__manager=self.request.user)
            stats.update({
                'total_employees': managed_employees.count(),
                'present_today': self._get_present_today_count(managed_employees),
                'absent_today': self._get_absent_today_count(managed_employees),
                'on_leave_today': self._get_on_leave_today_count(managed_employees),
                'pending_leave_requests': LeaveRequest.objects.filter(
                    employee__in=managed_employees, status='pending'
                ).count(),
            })
        else:
            # Statistiques pour employé (lui-même)
            stats.update({
                'present_today': self._get_present_today_count([self.request.user]),
                'leave_requests_pending': LeaveRequest.objects.filter(
                    employee=self.request.user, status='pending'
                ).count(),
                'anomalies_pending': AttendanceAnomaly.objects.filter(
                    attendance__employee=self.request.user, status='pending'
                ).count(),
            })
        
        return stats
    
    def _get_present_today_count(self, employees=None):
        """Compte les employés présents aujourd'hui."""
        if employees is None:
            employees = User.objects.filter(employee_profile__is_active=True)
        
        today = date.today()
        return Attendance.objects.filter(
            employee__in=employees,
            date=today,
            punch_type='in'
        ).count()
    
    def _get_absent_today_count(self, employees=None):
        """Compte les employés absents aujourd'hui."""
        if employees is None:
            employees = User.objects.filter(employee_profile__is_active=True)
        
        today = date.today()
        present_employees = Attendance.objects.filter(
            employee__in=employees,
            date=today,
            punch_type='in'
        ).values_list('employee', flat=True)
        
        on_leave_employees = LeaveRequest.objects.filter(
            employee__in=employees,
            status='approved_rh',
            start_date__lte=today,
            end_date__gte=today
        ).values_list('employee', flat=True)
        
        # Combiner les listes et exclure les employés présents ou en congé
        present_and_leave_ids = list(present_employees) + list(on_leave_employees)
        absent_count = employees.exclude(
            id__in=present_and_leave_ids
        ).count()
        
        return absent_count
    
    def _get_on_leave_today_count(self, employees=None):
        """Compte les employés en congé aujourd'hui."""
        if employees is None:
            employees = User.objects.filter(employee_profile__is_active=True)
        
        today = date.today()
        return LeaveRequest.objects.filter(
            employee__in=employees,
            status='approved_rh',
            start_date__lte=today,
            end_date__gte=today
        ).count()
    
    def _get_charts_data(self, today, profile):
        """Prépare les données pour les graphiques."""
        charts = {}
        
        # Graphique des présences des 30 derniers jours
        start_date = today - timedelta(days=30)
        charts['attendance_trend'] = self._get_attendance_trend(start_date, today, profile)
        
        # Graphique des congés par mois (6 derniers mois)
        charts['leave_trend'] = self._get_leave_trend(profile)
        
        # Graphique des départements
        charts['department_stats'] = self._get_department_stats(profile)
        
        return charts
    
    def _get_attendance_trend(self, start_date, end_date, profile):
        """Données pour le graphique de tendance des présences."""
        if profile.role == 'rh':
            # Toute l'entreprise
            attendance_data = Attendance.objects.filter(
                date__range=[start_date, end_date],
                punch_type='in'
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
        elif profile.role == 'manager':
            # Équipe du manager
            managed_employees = User.objects.filter(employee_profile__manager=self.request.user)
            attendance_data = Attendance.objects.filter(
                employee__in=managed_employees,
                date__range=[start_date, end_date],
                punch_type='in'
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
        else:
            # Employé individuel
            attendance_data = Attendance.objects.filter(
                employee=self.request.user,
                date__range=[start_date, end_date],
                punch_type='in'
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
        
        return list(attendance_data)
    
    def _get_leave_trend(self, profile):
        """Données pour le graphique de tendance des congés."""
        from django.db import connection
        
        # Utiliser la fonction appropriée selon la base de données
        if 'postgresql' in connection.vendor:
            date_func = "DATE_TRUNC('month', start_date)"
        else:
            # Pour SQLite
            date_func = "strftime('%%Y-%%m', start_date)"
        
        if profile.role == 'rh':
            # Toute l'entreprise
            leave_data = LeaveRequest.objects.filter(
                status='approved_rh',
                start_date__gte=date.today() - timedelta(days=180)
            ).extra(
                select={'month': date_func}
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')
        elif profile.role == 'manager':
            # Équipe du manager
            managed_employees = User.objects.filter(employee_profile__manager=self.request.user)
            leave_data = LeaveRequest.objects.filter(
                employee__in=managed_employees,
                status='approved_rh',
                start_date__gte=date.today() - timedelta(days=180)
            ).extra(
                select={'month': date_func}
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')
        else:
            # Employé individuel
            leave_data = LeaveRequest.objects.filter(
                employee=self.request.user,
                status='approved_rh',
                start_date__gte=date.today() - timedelta(days=180)
            ).extra(
                select={'month': date_func}
            ).values('month').annotate(
                count=Count('id')
            ).order_by('month')
        
        return list(leave_data)
    
    def _get_department_stats(self, profile):
        """Données pour le graphique des départements."""
        if profile.role == 'rh':
            # Toute l'entreprise
            dept_data = Department.objects.annotate(
                employee_count=Count('employees', filter=Q(employees__is_active=True))
            ).values('name', 'employee_count')
        elif profile.role == 'manager':
            # Équipe du manager
            dept_data = Department.objects.filter(
                employees__manager=self.request.user,
                employees__is_active=True
            ).annotate(
                employee_count=Count('employees')
            ).values('name', 'employee_count')
        else:
            # Employé individuel
            dept_data = Department.objects.filter(
                employees=self.request.user.employee_profile
            ).annotate(
                employee_count=Count('employees')
            ).values('name', 'employee_count')
        
        return list(dept_data)
    
    def _get_recent_reports(self):
        """Récupère les rapports récents."""
        # Ici on pourrait récupérer l'historique des rapports générés
        # Pour l'instant, on retourne les templates disponibles
        return ReportTemplate.objects.filter(is_active=True)[:5]


class AttendanceReportView(LoginRequiredMixin, TemplateView):
    """
    Rapport de présence détaillé.
    """
    template_name = 'reports/attendance_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = user.employee_profile
        
        # Paramètres du rapport
        start_date = self.request.GET.get('start_date', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = self.request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))
        department_id = self.request.GET.get('department')
        employee_id = self.request.GET.get('employee')
        
        # Conversion des dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'departments': Department.objects.all(),
            'selected_department': department_id,
            'selected_employee': employee_id,
        })
        
        # Données du rapport
        context.update(self._get_attendance_data(start_date, end_date, department_id, employee_id, profile))
        
        return context
    
    def _get_attendance_data(self, start_date, end_date, department_id, employee_id, profile):
        """Récupère les données de présence pour le rapport."""
        data = {}
        
        # Déterminer les employés à inclure
        if profile.role == 'rh':
            # Tous les employés
            if department_id:
                employees = User.objects.filter(
                    employee_profile__department_id=department_id,
                    employee_profile__is_active=True
                )
            elif employee_id:
                employees = User.objects.filter(id=employee_id)
            else:
                employees = User.objects.filter(employee_profile__is_active=True)
        elif profile.role == 'manager':
            # Équipe du manager
            employees = User.objects.filter(
                employee_profile__manager=self.request.user,
                employee_profile__is_active=True
            )
        else:
            # Employé individuel
            employees = User.objects.filter(id=self.request.user.id)
        
        # Données de présence
        attendance_records = Attendance.objects.filter(
            employee__in=employees,
            date__range=[start_date, end_date]
        ).select_related('employee', 'employee__employee_profile')
        
        # Statistiques par employé
        employee_stats = []
        for employee in employees:
            emp_attendance = attendance_records.filter(employee=employee)
            
            # Calcul des statistiques
            total_days = (end_date - start_date).days + 1
            present_days = emp_attendance.filter(punch_type='in').count()
            absent_days = total_days - present_days
            
            # Heures de travail (estimation basée sur les pointages)
            # Pour l'instant, on estime 8h par jour de présence
            total_hours = present_days * 8
            
            employee_stats.append({
                'employee': employee,
                'total_days': total_days,
                'present_days': present_days,
                'absent_days': absent_days,
                'attendance_rate': (present_days / total_days * 100) if total_days > 0 else 0,
                'total_hours': total_hours,
                'attendance_records': emp_attendance.order_by('date', 'time'),
            })
        
        data.update({
            'employee_stats': employee_stats,
            'total_employees': len(employee_stats),
            'period_days': (end_date - start_date).days + 1,
        })
        
        return data


class LeaveReportView(LoginRequiredMixin, TemplateView):
    """
    Rapport de congés détaillé.
    """
    template_name = 'reports/leave_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = user.employee_profile
        
        # Paramètres du rapport
        year = int(self.request.GET.get('year', date.today().year))
        leave_type_id = self.request.GET.get('leave_type')
        status = self.request.GET.get('status')
        
        context.update({
            'year': year,
            'leave_types': LeaveType.objects.filter(is_active=True),
            'selected_leave_type': leave_type_id,
            'selected_status': status,
        })
        
        # Données du rapport
        context.update(self._get_leave_data(year, leave_type_id, status, profile))
        
        return context
    
    def _get_leave_data(self, year, leave_type_id, status, profile):
        """Récupère les données de congés pour le rapport."""
        data = {}
        
        # Filtres de base
        filters = {
            'start_date__year': year,
        }
        
        if leave_type_id:
            filters['leave_type_id'] = leave_type_id
        if status:
            filters['status'] = status
        
        # Déterminer les employés à inclure
        if profile.role == 'rh':
            # Tous les employés
            leave_requests = LeaveRequest.objects.filter(**filters)
        elif profile.role == 'manager':
            # Équipe du manager
            managed_employees = User.objects.filter(employee_profile__manager=self.request.user)
            leave_requests = LeaveRequest.objects.filter(
                employee__in=managed_employees,
                **filters
            )
        else:
            # Employé individuel
            leave_requests = LeaveRequest.objects.filter(
                employee=self.request.user,
                **filters
            )
        
        # Statistiques générales
        total_requests = leave_requests.count()
        approved_requests = leave_requests.filter(status__in=['approved_manager', 'approved_rh']).count()
        rejected_requests = leave_requests.filter(status__in=['rejected_manager', 'rejected_rh']).count()
        pending_requests = leave_requests.filter(status='pending').count()
        
        # Statistiques par type de congé
        leave_type_stats = []
        for leave_type in LeaveType.objects.filter(is_active=True):
            type_requests = leave_requests.filter(leave_type=leave_type)
            type_stats = {
                'leave_type': leave_type,
                'total_requests': type_requests.count(),
                'approved_requests': type_requests.filter(status__in=['approved_manager', 'approved_rh']).count(),
                'total_days': type_requests.filter(status__in=['approved_manager', 'approved_rh']).aggregate(
                    total=Sum('duration_days')
                )['total'] or 0,
            }
            leave_type_stats.append(type_stats)
        
        # Statistiques par mois
        monthly_stats = []
        for month in range(1, 13):
            month_requests = leave_requests.filter(start_date__month=month)
            monthly_stats.append({
                'month': month,
                'month_name': date(year, month, 1).strftime('%B'),
                'total_requests': month_requests.count(),
                'approved_requests': month_requests.filter(status__in=['approved_manager', 'approved_rh']).count(),
                'total_days': month_requests.filter(status__in=['approved_manager', 'approved_rh']).aggregate(
                    total=Sum('duration_days')
                )['total'] or 0,
            })
        
        data.update({
            'leave_requests': leave_requests.select_related('employee', 'leave_type').order_by('-created_at'),
            'total_requests': total_requests,
            'approved_requests': approved_requests,
            'rejected_requests': rejected_requests,
            'pending_requests': pending_requests,
            'leave_type_stats': leave_type_stats,
            'monthly_stats': monthly_stats,
        })
        
        return data


class AnomalyReportView(LoginRequiredMixin, TemplateView):
    """
    Rapport d'anomalies de présence.
    """
    template_name = 'reports/anomaly_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile = user.employee_profile
        
        # Paramètres du rapport
        start_date = self.request.GET.get('start_date', (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = self.request.GET.get('end_date', date.today().strftime('%Y-%m-%d'))
        anomaly_type = self.request.GET.get('anomaly_type')
        
        # Conversion des dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = date.today() - timedelta(days=30)
            end_date = date.today()
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'selected_anomaly_type': anomaly_type,
        })
        
        # Données du rapport
        context.update(self._get_anomaly_data(start_date, end_date, anomaly_type, profile))
        
        return context
    
    def _get_anomaly_data(self, start_date, end_date, anomaly_type, profile):
        """Récupère les données d'anomalies pour le rapport."""
        data = {}
        
        # Filtres de base
        filters = {
            'attendance__date__range': [start_date, end_date],
        }
        
        if anomaly_type:
            filters['anomaly_type'] = anomaly_type
        
        # Déterminer les employés à inclure
        if profile.role == 'rh':
            # Toutes les anomalies
            anomalies = AttendanceAnomaly.objects.filter(**filters)
        elif profile.role == 'manager':
            # Anomalies de l'équipe
            managed_employees = User.objects.filter(employee_profile__manager=self.request.user)
            anomalies = AttendanceAnomaly.objects.filter(
                attendance__employee__in=managed_employees,
                **filters
            )
        else:
            # Anomalies de l'employé
            anomalies = AttendanceAnomaly.objects.filter(
                attendance__employee=self.request.user,
                **filters
            )
        
        # Statistiques par type d'anomalie
        anomaly_type_stats = anomalies.values('anomaly_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Statistiques par employé
        employee_anomaly_stats = anomalies.values(
            'attendance__employee__username',
            'attendance__employee__first_name',
            'attendance__employee__last_name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        data.update({
            'anomalies': anomalies.select_related('attendance__employee').order_by('-created_at'),
            'anomaly_type_stats': list(anomaly_type_stats),
            'employee_anomaly_stats': list(employee_anomaly_stats),
            'total_anomalies': anomalies.count(),
        })
        
        return data


@login_required
def export_report_api(request):
    """
    API pour l'export de rapports en différents formats.
    """
    from .export_services import PDFExportService, ExcelExportService
    
    report_type = request.GET.get('type')
    format_type = request.GET.get('format', 'pdf')
    
    try:
        if report_type == 'attendance':
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            department_id = request.GET.get('department')
            
            # Conversion des dates
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else date.today() - timedelta(days=30)
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else date.today()
            
            if format_type == 'pdf':
                pdf_service = PDFExportService()
                return pdf_service.export_attendance_report(request, start_date, end_date, department_id)
            elif format_type == 'excel':
                excel_service = ExcelExportService()
                return excel_service.export_attendance_report(request, start_date, end_date, department_id)
        
        elif report_type == 'leave':
            year = int(request.GET.get('year', date.today().year))
            leave_type_id = request.GET.get('leave_type')
            status = request.GET.get('status')
            
            if format_type == 'pdf':
                pdf_service = PDFExportService()
                return pdf_service.export_leave_report(request, year, leave_type_id, status)
            elif format_type == 'excel':
                excel_service = ExcelExportService()
                return excel_service.export_leave_report(request, year, leave_type_id, status)
        
        # Exports inutiles supprimés - garder seulement les rapports avec valeur ajoutée
        
        elif report_type == 'summary':
            # Export récapitulatif
            if format_type == 'pdf':
                pdf_service = PDFExportService()
                # Pour l'instant, on exporte le rapport de présence du mois
                start_date = date.today().replace(day=1)
                end_date = date.today()
                return pdf_service.export_attendance_report(request, start_date, end_date)
            elif format_type == 'excel':
                excel_service = ExcelExportService()
                start_date = date.today().replace(day=1)
                end_date = date.today()
                return excel_service.export_attendance_report(request, start_date, end_date)
        
        else:
            return JsonResponse({'error': 'Type de rapport non supporté'}, status=400)
    
    except Exception as e:
        # En cas d'erreur, retourner un message d'erreur avec plus de détails
        import traceback
        error_details = traceback.format_exc()
        print(f"Erreur export: {e}")
        print(f"Details: {error_details}")
        return JsonResponse({
            'error': 'Erreur lors de l\'export',
            'details': str(e),
            'traceback': error_details
        }, status=500)


@login_required
def critical_stats_api(request):
    """
    API pour les statistiques critiques importantes.
    Retourne les métriques essentielles pour la gestion d'entreprise.
    """
    from datetime import date, timedelta
    from django.db.models import Count, Sum, Avg
    from attendance.models import Attendance
    from leave.models import LeaveRequest
    # NOTE: OvertimeRecord n'existe pas encore dans le projet
    # from attendance.overtime_models import OvertimeRecord
    
    try:
        user = request.user
        profile = user.employee_profile
        
        # Période : 6 derniers mois
        end_date = date.today()
        start_date = end_date - timedelta(days=180)
        
        stats = {}
        
        if profile.role == 'rh':
            # === STATISTIQUES GLOBALES ===
            
            # 1. TAUX DE PRÉSENCE GLOBAL (6 mois)
            total_working_days = 130  # Estimation 6 mois
            total_possible_presences = EmployeeProfile.objects.filter(
                is_active=True
            ).exclude(role='rh').count() * total_working_days
            
            total_presences = Attendance.objects.filter(
                date__range=[start_date, end_date],
                punch_type='in',
                employee__employee_profile__is_active=True
            ).exclude(
                employee__employee_profile__role='rh'
            ).count()
            
            taux_presence = (total_presences / total_possible_presences * 100) if total_possible_presences > 0 else 0
            
            # 2. ÉVOLUTION ABSENTÉISME (6 mois)
            evolution_absences = []
            for i in range(6):
                month_start = end_date - timedelta(days=30*(i+1))
                month_end = end_date - timedelta(days=30*i)
                
                month_presences = Attendance.objects.filter(
                    date__range=[month_start, month_end],
                    punch_type='in'
                ).exclude(
                    employee__employee_profile__role='rh'
                ).count()
                
                month_possible = EmployeeProfile.objects.filter(
                    is_active=True
                ).exclude(role='rh').count() * 22  # 22 jours ouvrables/mois
                
                month_rate = (month_presences / month_possible * 100) if month_possible > 0 else 0
                evolution_absences.append({
                    'mois': month_start.strftime('%Y-%m'),
                    'taux_presence': round(month_rate, 1)
                })
            
            # 3. HEURES SUPPLÉMENTAIRES (6 mois)
            # NOTE: OvertimeRecord n'existe pas encore - désactivé temporairement
            # overtime_total = OvertimeRecord.objects.filter(
            #     date__range=[start_date, end_date],
            #     status='approved'
            # ).aggregate(total=Sum('overtime_hours'))['total'] or 0
            overtime_total = 0  # Temporaire
            
            # overtime_avg_per_employee = overtime_total / EmployeeProfile.objects.filter(
            #     is_active=True
            # ).exclude(role='rh').count() if EmployeeProfile.objects.filter(
            #     is_active=True
            # ).exclude(role='rh'
            # ).count() > 0 else 0
            overtime_avg_per_employee = 0  # Temporaire
            
            # 4. CONGÉS - UTILISATION
            leaves_used = LeaveRequest.objects.filter(
                start_date__range=[start_date, end_date],
                status__in=['approved_manager', 'approved_rh']
            ).aggregate(total=Sum('duration_days'))['total'] or 0
            
            stats = {
                'taux_presence_global': round(taux_presence, 1),
                'evolution_6_mois': list(reversed(evolution_absences)),
                'heures_supp_total': overtime_total,
                'heures_supp_moyenne_employe': round(overtime_avg_per_employee, 1),
                'conges_utilises_6_mois': leaves_used,
                'alertes': []
            }
            
            # Alertes critiques
            if taux_presence < 90:
                stats['alertes'].append({
                    'type': 'warning',
                    'message': f'Taux de présence faible: {taux_presence:.1f}%'
                })
            
            if overtime_avg_per_employee > 10:
                stats['alertes'].append({
                    'type': 'info',
                    'message': f'Heures supplémentaires élevées: {overtime_avg_per_employee:.1f}h/employé'
                })
        
        elif profile.role == 'manager':
            # === STATISTIQUES MANAGER (son équipe) ===
            managed_employees = User.objects.filter(employee_profile__manager=user)
            
            # Taux de présence de l'équipe
            team_presences = Attendance.objects.filter(
                date__range=[start_date, end_date],
                punch_type='in',
                employee__in=managed_employees
            ).count()
            
            team_possible = managed_employees.count() * 130  # 6 mois
            team_rate = (team_presences / team_possible * 100) if team_possible > 0 else 0
            
            stats = {
                'taux_presence_equipe': round(team_rate, 1),
                'effectif': managed_employees.count(),
                'conges_en_attente': LeaveRequest.objects.filter(
                    employee__in=managed_employees,
                    status='pending'
                ).count()
            }
        
        else:
            # === STATISTIQUES EMPLOYÉ ===
            user_presences = Attendance.objects.filter(
                date__range=[start_date, end_date],
                punch_type='in',
                employee=user
            ).count()
            
            user_rate = (user_presences / 130) * 100  # 6 mois
            
            stats = {
                'taux_presence_personnel': round(user_rate, 1),
                'conges_restants': 25 - LeaveRequest.objects.filter(
                    employee=user,
                    status__in=['approved_manager', 'approved_rh'],
                    start_date__year=date.today().year
                ).aggregate(total=Sum('duration_days'))['total'] or 0
            }
        
        return JsonResponse(stats)
    
    except Exception as e:
        return JsonResponse({
            'error': 'Erreur lors du calcul des statistiques',
            'details': str(e)
        }, status=500)
