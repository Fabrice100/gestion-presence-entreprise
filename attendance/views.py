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
from datetime import date, timedelta, datetime
from decimal import Decimal
from django_ratelimit.decorators import ratelimit
from django.conf import settings
from common.error_handler import handle_errors, ErrorContext, ErrorCode, ErrorSeverity
# Modules de performance simplifiés - désactivés pour projet de fin de cycle
# from common.query_optimizer import query_optimizer, pagination_optimizer
# from common.intelligent_cache import intelligent_cache, CacheStrategy

from .models import Attendance

# Import du mixin centralisé (principe DRY)
from common.mixins import EnhancedLoginRequiredMixin, EmployeeRequiredMixin


class PunchView(EmployeeRequiredMixin, TemplateView):
    """Vue principale pour le pointage."""
    template_name = 'attendance/punch_ultra_modern.html'

    def dispatch(self, request, *args, **kwargs):
        profile = getattr(request.user, 'employee_profile', None)

        if profile is None:
            messages.error(request, "Vous n'avez pas de profil employé. Contactez l'administrateur.")
            return redirect('dashboard:dashboard')

        if profile.role == 'rh':
            messages.info(request, "Les comptes RH ne pointent pas dans l'application.")
            return redirect('dashboard:rh_dashboard')

        if not profile.can_punch:
            messages.error(request, "Vous n'êtes pas autorisé à pointer.")
            return redirect('dashboard:dashboard')

        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        
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
        """Filtre et agrège les présences par date."""
        # Requête de base optimisée
        queryset = Attendance.objects.filter(
            employee=self.request.user
        ).select_related('employee').order_by('-date', 'time')
        
        # Filtres de date
        today = timezone.now().date()
        start_date = self.request.GET.get('date_from')
        end_date = self.request.GET.get('date_to')
        
        if start_date:
            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
            queryset = queryset.filter(date__gte=start_date)
        else:
            start_date = today - timedelta(days=30)
            queryset = queryset.filter(date__gte=start_date)
        
        if end_date:
            if isinstance(end_date, str):
                end_date = date.fromisoformat(end_date)
            queryset = queryset.filter(date__lte=end_date)
        else:
            end_date = today
            queryset = queryset.filter(date__lte=end_date)
        
        # Agréger les pointages par date
        from collections import defaultdict
        aggregated = defaultdict(lambda: {
            'date': None,
            'check_in': None,
            'check_out': None,
            'total_hours': None,
            'worked_hours': None
        })
        
        for att in queryset:
            att_date = att.date
            if not aggregated[att_date]['date']:
                aggregated[att_date]['date'] = att_date
            
            if att.punch_type == 'in':
                aggregated[att_date]['check_in'] = att.time
            elif att.punch_type == 'out':
                aggregated[att_date]['check_out'] = att.time
                # Utiliser worked_hours s'il existe, sinon calculer à partir de check_in/check_out
                if att.worked_hours is not None:
                    aggregated[att_date]['worked_hours'] = att.worked_hours
                    total_decimal = float(att.worked_hours)
                    aggregated[att_date]['total_hours'] = f"{total_decimal:.2f}h"
        
        # Calculer la durée pour les jours avec entrée ET sortie mais sans worked_hours
        from attendance.hours_calculation_service import HoursCalculationService
        
        for att_date in aggregated.keys():
            data = aggregated[att_date]
            if data['check_in'] and data['check_out'] and not data['total_hours']:
                # Utiliser le service de calcul qui prend en compte le profil horaire
                try:
                    employee_profile = self.request.user.employee_profile
                    worked_hours = HoursCalculationService.calculate_worked_hours(
                        data['check_in'],
                        data['check_out'],
                        employee_profile=employee_profile,
                        attendance_date=att_date
                    )
                except Exception:
                    # Fallback: calcul simple sans profil horaire
                    worked_hours = HoursCalculationService.calculate_worked_hours(
                        data['check_in'],
                        data['check_out']
                    )
                
                # Formater avec 2 décimales
                total_decimal = float(worked_hours)
                aggregated[att_date]['total_hours'] = f"{total_decimal:.2f}h"
                aggregated[att_date]['worked_hours'] = worked_hours
        
        # Convertir en liste et trier par date (plus récent en premier)
        result = []
        for att_date in sorted(aggregated.keys(), reverse=True):
            data = aggregated[att_date]
            # Créer un objet simple avec les attributs nécessaires
            class AttendanceDay:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
            
            result.append(AttendanceDay(**data))
        
        return result
    
    def get_context_data(self, **kwargs):
        """Ajoute des données de contexte optimisées."""
        context = super().get_context_data(**kwargs)
        
        # Statistiques de base
        current_year = timezone.now().year
        attendances_count = len(self.get_queryset())
        
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
        """Vérifier que l'utilisateur est manager ou RH"""
        if not hasattr(request.user, 'employee_profile'):
            messages.error(request, 'Vous n\'avez pas de profil employé.')
            return redirect('dashboard:manager_dashboard')
        
        profile = request.user.employee_profile
        if profile.role not in ['manager', 'rh', 'dg']:
            messages.error(request, 'Accès réservé aux managers et RH.')
            return redirect('dashboard:manager_dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filtre les présences selon le rôle et les filtres"""
        profile = self.request.user.employee_profile
        
        # Base queryset selon le rôle
        if profile.role == 'manager':
            # Manager ne voit que son département
            queryset = Attendance.objects.filter(
                employee__employee_profile__department=profile.department
            )
        else:
            # RH voit tout
            queryset = Attendance.objects.all()
        
        queryset = queryset.select_related('employee', 'employee__employee_profile').order_by('-date', '-time')
        
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
            # Le département peut être un ID ou un nom
            try:
                from accounts.models import Department
                dept = Department.objects.filter(name=department).first()
                if dept:
                    queryset = queryset.filter(employee__employee_profile__department=dept)
            except:
                pass
        
        # Filtre par employé
        employee_id = self.request.GET.get('employee')
        if employee_id:
            queryset = queryset.filter(employee__employee_profile__employee_id=employee_id)
        
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
        from accounts.models import EmployeeProfile, Department
        if self.request.user.employee_profile.role in ['rh', 'dg']:
            context['departments'] = Department.objects.values_list('name', flat=True).distinct()
        
        return context



