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
    template_name = 'attendance/punch.html'
    
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
    template_name = 'attendance/my_attendance.html'
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

