"""
Vues pour l'application attendance (pointage et présence).

Ce module contient les vues pour :
- Pointage d'entrée et de sortie
- Consultation des présences
- Gestion des anomalies
- Rapports de présence

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, DetailView
from django.utils import timezone
from django.db.models import Q
from datetime import date, timedelta
from django_ratelimit.decorators import ratelimit
from django.conf import settings
from common.error_handler import handle_errors, ErrorContext, ErrorCode, ErrorSeverity
from common.query_optimizer import query_optimizer, pagination_optimizer
from common.intelligent_cache import intelligent_cache, CacheStrategy

from .models import Attendance, AttendanceAnomaly

# Import du mixin centralisé (principe DRY)
from common.mixins import EnhancedLoginRequiredMixin, EmployeeRequiredMixin


class PunchView(EmployeeRequiredMixin, TemplateView):
    """Vue principale pour le pointage."""
    template_name = 'attendance/punch_ultra_modern.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        
        # Vérifier si l'utilisateur peut pointer
        try:
            if not user.employee_profile.can_punch:
                messages.error(self.request, 'Vous n\'êtes pas autorisé à pointer.')
                return redirect('dashboard:dashboard')
        except:
            messages.error(self.request, 'Vous n\'avez pas de profil employé. Contactez l\'administrateur.')
            return redirect('dashboard:dashboard')
        
        # Pointages du jour
        today_attendance = Attendance.objects.filter(
            employee=user,
            date=today
        ).order_by('time')
        
        # Dernier pointage
        last_attendance = Attendance.objects.filter(
            employee=user
        ).order_by('-date', '-time').first()
        
        # Déterminer le prochain type de pointage
        next_punch_type = 'in'
        if last_attendance and last_attendance.date == today:
            if last_attendance.punch_type == 'in':
                next_punch_type = 'out'
            else:
                next_punch_type = 'in'
        
        context.update({
            'today_attendance': today_attendance,
            'last_attendance': last_attendance,
            'next_punch_type': next_punch_type,
            'today': today,
        })
        
        return context
    
    @method_decorator(ratelimit(key='user', rate=settings.RATELIMIT_PUNCH_RATE, method='POST', block=True))
    @handle_errors(error_type="punch_operation", severity=ErrorSeverity.MEDIUM)
    def post(self, request, *args, **kwargs):
        """
        Traite le pointage via POST avec le service unifié.
        
        VERSION ULTRA-REFACTORISÉE - Respecte parfaitement les principes SOLID :
        - Single Responsibility: La vue ne fait que coordonner
        - Open/Closed: Extensible via injection de dépendances
        - Dependency Inversion: Utilise PunchService (abstraction)
        
        Cette méthode est réduite de 200 lignes à ~30 lignes en utilisant
        le PunchService unifié qui centralise toute la logique métier.
        """
        from .forms import PunchForm
        from .services import PunchService
        
        # 1. VALIDATION DES DONNÉES ENTRANTES
        form = PunchForm(request.POST)
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect('attendance:punch')
        
        # 2. PRÉPARATION DES DONNÉES
        gps_data = form.get_gps_data()
        request_meta = {
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
        }
        
        # 3. POINTAGE UNIFIÉ (toute la logique métier dans le service)
        punch_service = PunchService()
        result = punch_service.create_punch(
            user=request.user,
            punch_type=form.cleaned_data['punch_type'],
            gps_data=gps_data,
            request_meta=request_meta
        )
        
        # 4. GESTION DES RÉSULTATS
        if result.is_success():
            # Message de succès
            punch_type_label = 'entrée' if result.attendance.punch_type == 'in' else 'sortie'
            messages.success(
                request,
                f'✅ Pointage {punch_type_label} enregistré avec succès à {result.attendance.time.strftime("%H:%M")}.'
            )
            
            # Avertissement GPS si nécessaire
            if result.has_warning():
                messages.warning(request, result.warning_message)
        else:
            # Message d'erreur
            messages.error(request, result.error_message)
        
        return redirect('attendance:punch')
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class MyAttendanceView(EmployeeRequiredMixin, ListView):
    """Vue optimisée pour consulter ses propres pointages."""
    model = Attendance
    template_name = 'attendance/my_attendance_ultra_modern.html'
    context_object_name = 'attendances'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtre les présences avec optimisations de performance."""
        # Requête de base optimisée
        queryset = Attendance.objects.filter(
            employee=self.request.user
        ).select_related('employee').order_by('-date', '-time')
        
        # Filtres de date
        today = timezone.now().date()
        start_date = self.request.GET.get('date_from', today - timedelta(days=30))
        end_date = self.request.GET.get('date_to', today)
        
        # Conversion des dates si nécessaire
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
        
        queryset = queryset.filter(date__range=[start_date, end_date])
        
        # Filtres supplémentaires
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Ajoute des données de contexte optimisées."""
        context = super().get_context_data(**kwargs)
        
        # Statistiques de base
        current_year = timezone.now().year
        attendances_count = self.get_queryset().count()
        
        context.update({
            'attendance_count': attendances_count,
            'current_year': current_year,
            'today': timezone.now().date()
        })
        
        return context


class TeamAttendanceView(EnhancedLoginRequiredMixin, ListView):
    """
    Vue pour les managers: visualiser les pointages de toute l'équipe
    Filtres: département, date, statut
    Export: Excel
    """
    model = Attendance
    template_name = 'attendance/team_attendance_ultra_modern.html'
    context_object_name = 'attendances'
    paginate_by = 50
    
    def dispatch(self, request, *args, **kwargs):
        """Vérifier que l'utilisateur est manager ou RH/DG"""
        if not hasattr(request.user, 'employeeprofile'):
            messages.error(request, 'Vous n\'avez pas de profil employé.')
            return redirect('dashboard:main')
        
        profile = request.user.employeeprofile
        if profile.role not in ['manager', 'rh', 'dg']:
            messages.error(request, 'Accès réservé aux managers et RH.')
            return redirect('dashboard:main')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filtre les présences selon le rôle et les filtres"""
        profile = self.request.user.employeeprofile
        
        # Base queryset selon le rôle
        if profile.role == 'manager':
            # Manager ne voit que son département
            queryset = Attendance.objects.filter(
                employee__employeeprofile__department=profile.department
            )
        else:
            # RH/DG voit tout
            queryset = Attendance.objects.all()
        
        queryset = queryset.select_related('employee', 'employee__employeeprofile').order_by('-date', '-time')
        
        # Filtres de date
        today = timezone.now().date()
        start_date = self.request.GET.get('date_from', today - timedelta(days=7))
        end_date = self.request.GET.get('date_to', today)
        
        if isinstance(start_date, str):
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            from datetime import datetime
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        queryset = queryset.filter(date__range=[start_date, end_date])
        
        # Filtre par département
        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(employee__employeeprofile__department=department)
        
        # Filtre par employé
        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee__employeeprofile__employee_id=employee_id)
        
        # Filtre par type de pointage
        punch_type = self.request.GET.get('type')
        if punch_type:
            queryset = queryset.filter(punch_type=punch_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        attendances = self.get_queryset()
        context.update({
            'total_attendances': attendances.count(),
            'punch_in_count': attendances.filter(punch_type='in').count(),
            'punch_out_count': attendances.filter(punch_type='out').count(),
            'today': timezone.now().date(),
            'seven_days_ago': timezone.now().date() - timedelta(days=7),
        })
        
        # Liste des départements pour le filtre
        from accounts.models import EmployeeProfile
        if self.request.user.employeeprofile.role in ['rh', 'dg']:
            context['departments'] = EmployeeProfile.objects.values_list('department', flat=True).distinct()
        
        return context


class AnomaliesManagementView(EnhancedLoginRequiredMixin, ListView):
    """
    Vue RH/DG pour gérer les anomalies de pointage
    Détection automatique, filtres, actions en masse
    """
    model = AttendanceAnomaly
    template_name = 'attendance/anomalies_management_ultra_modern.html'
    context_object_name = 'anomalies'
    paginate_by = 30
    
    def dispatch(self, request, *args, **kwargs):
        """Vérifier que l'utilisateur est RH/DG"""
        if not hasattr(request.user, 'employeeprofile'):
            messages.error(request, 'Vous n\'avez pas de profil employé.')
            return redirect('dashboard:main')
        
        profile = request.user.employeeprofile
        if profile.role not in ['rh', 'dg']:
            messages.error(request, 'Accès réservé aux RH et DG.')
            return redirect('dashboard:main')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filtre les anomalies selon les critères"""
        queryset = AttendanceAnomaly.objects.all().select_related(
            'employee', 'employee__employeeprofile', 'attendance'
        ).order_by('-created_at')
        
        # Filtre par type d'anomalie
        anomaly_type = self.request.GET.get('anomaly_type')
        if anomaly_type:
            queryset = queryset.filter(anomaly_type=anomaly_type)
        
        # Filtre par statut
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filtre par période
        period = self.request.GET.get('period', '7')
        try:
            days = int(period)
            from_date = timezone.now().date() - timedelta(days=days)
            queryset = queryset.filter(date__gte=from_date)
        except:
            pass
        
        # Recherche par nom
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(employee__first_name__icontains=search) |
                Q(employee__last_name__icontains=search) |
                Q(employee__employeeprofile__employee_id__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        all_anomalies = AttendanceAnomaly.objects.all()
        context['stats'] = {
            'active_count': all_anomalies.filter(status='pending').count(),
            'resolved_count': all_anomalies.filter(status='resolved').count(),
            'pending_count': all_anomalies.filter(status='reviewed').count(),
            'this_week_count': all_anomalies.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'missing_punches_count': all_anomalies.filter(anomaly_type='missing_punch').count(),
            'suspect_hours_count': all_anomalies.filter(
                anomaly_type__in=['late_arrival', 'early_departure']
            ).count(),
            'gps_anomalies_count': all_anomalies.filter(anomaly_type='gps_out_of_range').count(),
        }
        
        return context


