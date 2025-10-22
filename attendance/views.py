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
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import date, timedelta
import json

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
    
    def post(self, request, *args, **kwargs):
        """
        Traite le pointage via POST avec validation GPS et règles métier.
        
        VERSION REFACTORISÉE - Respecte les principes SOLID :
        - Single Responsibility: Chaque service a une responsabilité unique
        - Dependency Inversion: Utilise des abstractions (services)
        
        Cette méthode est réduite de 200 lignes à ~80 lignes en extrayant
        la logique vers GPSValidationService, AttendanceBusinessRules et AttendanceService.
        """
        from .forms import PunchForm
        from .attendance_service import (
            GPSValidationService,
            AttendanceBusinessRules,
            AttendanceService
        )
        from .admin_models import CompanySettings
        
        # 1. VALIDATION DES DONNÉES ENTRANTES (via Form)
        form = PunchForm(request.POST)
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return redirect('attendance:punch')
        
        # 2. VÉRIFICATION DES PERMISSIONS (via BusinessRules)
        can_punch, error = AttendanceBusinessRules.can_user_punch(request.user)
        if not can_punch:
            messages.error(request, error)
            return redirect('dashboard:dashboard')
        
        # 3. CHARGER LA CONFIGURATION
        settings = CompanySettings.load()
        
        # 4. PARSER LES DONNÉES GPS (via Service)
        gps_form_data = form.get_gps_data()
        gps_parsed = GPSValidationService.parse_gps_data(
            str(gps_form_data['latitude']) if gps_form_data['latitude'] else '',
            str(gps_form_data['longitude']) if gps_form_data['longitude'] else '',
            str(gps_form_data['accuracy']),
            demo_mode=gps_form_data['demo_mode'],
            settings=settings
        )
        
        if not gps_parsed['valid']:
            messages.error(request, gps_parsed['error_message'])
            return redirect('attendance:punch')
        
        # Avertissement si GPS non disponible
        if gps_parsed.get('warning'):
            messages.warning(request, gps_parsed['warning'])
        
        # 5. VALIDATION GPS (via Service)
        validation_result = GPSValidationService.validate_location(
            gps_parsed['latitude'],
            gps_parsed['longitude'],
            gps_parsed['accuracy'],
            float(settings.site_center_latitude),
            float(settings.site_center_longitude),
            settings.allowed_radius_meters,
            settings.gps_accuracy_max_meters
        )
        
        if not validation_result['valid']:
            messages.error(request, validation_result['error_message'])
            return redirect('attendance:punch')
        
        # 6. CRÉER LE POINTAGE (via Service)
        gps_data = {
            'latitude': gps_parsed['latitude'],
            'longitude': gps_parsed['longitude'],
            'accuracy': gps_parsed['accuracy'],
            'distance': validation_result['distance']
        }
        
        request_meta = {
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
        }
        
        attendance, error = AttendanceService.create_punch(
            request.user,
            form.cleaned_data['punch_type'],
            gps_data,
            request_meta
        )
        
        if error:
            messages.error(request, error)
            return redirect('attendance:punch')
        
        # 7. MESSAGE DE SUCCÈS
        punch_type_label = 'entrée' if attendance.punch_type == 'in' else 'sortie'
        messages.success(
            request,
            f'✅ Pointage {punch_type_label} enregistré avec succès à {attendance.time.strftime("%H:%M")}.'
        )
        
        return redirect('attendance:punch')
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PunchInView(EmployeeRequiredMixin, CreateView):
    """Vue pour le pointage d'entrée."""
    model = Attendance
    fields = ['notes']
    template_name = 'attendance/punch_in.html'
    
    def form_valid(self, form):
        """Sauvegarde le pointage d'entrée."""
        user = self.request.user
        today = date.today()
        
        # Vérifier si l'utilisateur peut pointer
        if not user.employee_profile.can_punch:
            messages.error(self.request, 'Vous n\'êtes pas autorisé à pointer.')
            return redirect('dashboard:dashboard')
        
        # Vérifier si déjà pointé aujourd'hui
        existing_punch = Attendance.objects.filter(
            employee=user,
            date=today,
            punch_type='in'
        ).exists()
        
        if existing_punch:
            messages.warning(self.request, 'Vous avez déjà pointé l\'entrée aujourd\'hui.')
            return redirect('attendance:punch')
        
        # Créer le pointage
        attendance = form.save(commit=False)
        attendance.employee = user
        attendance.date = today
        attendance.time = timezone.now().time()
        attendance.punch_type = 'in'
        attendance.source = 'web'
        attendance.user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        attendance.ip_address = self.get_client_ip()
        
        # Coordonnées GPS (seront ajoutées via JavaScript)
        attendance.latitude = 0.0
        attendance.longitude = 0.0
        attendance.accuracy = 0.0
        
        attendance.save()
        
        messages.success(self.request, 'Pointage d\'entrée enregistré avec succès !')
        return redirect('attendance:punch')
    
    def get_client_ip(self):
        """Récupère l'adresse IP du client."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class PunchOutView(EmployeeRequiredMixin, CreateView):
    """Vue pour le pointage de sortie."""
    model = Attendance
    fields = ['notes']
    template_name = 'attendance/punch_out.html'
    
    def form_valid(self, form):
        """Sauvegarde le pointage de sortie."""
        user = self.request.user
        today = date.today()
        
        # Vérifier si l'utilisateur peut pointer
        if not user.employee_profile.can_punch:
            messages.error(self.request, 'Vous n\'êtes pas autorisé à pointer.')
            return redirect('dashboard:dashboard')
        
        # Vérifier si déjà pointé aujourd'hui
        existing_punch = Attendance.objects.filter(
            employee=user,
            date=today,
            punch_type='out'
        ).exists()
        
        if existing_punch:
            messages.warning(self.request, 'Vous avez déjà pointé la sortie aujourd\'hui.')
            return redirect('attendance:punch')
        
        # Vérifier s'il y a un pointage d'entrée
        punch_in = Attendance.objects.filter(
            employee=user,
            date=today,
            punch_type='in'
        ).first()
        
        if not punch_in:
            messages.error(self.request, 'Vous devez d\'abord pointer l\'entrée.')
            return redirect('attendance:punch')
        
        # Créer le pointage
        attendance = form.save(commit=False)
        attendance.employee = user
        attendance.date = today
        attendance.time = timezone.now().time()
        attendance.punch_type = 'out'
        attendance.source = 'web'
        attendance.user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        attendance.ip_address = self.get_client_ip()
        
        # Coordonnées GPS (seront ajoutées via JavaScript)
        attendance.latitude = 0.0
        attendance.longitude = 0.0
        attendance.accuracy = 0.0
        
        attendance.save()
        
        # Calculer la durée travaillée
        duration = attendance.get_duration_with_previous()
        if duration:
            messages.success(
                self.request, 
                f'Pointage de sortie enregistré ! Durée travaillée : {duration:.1f} heures.'
            )
        else:
            messages.success(self.request, 'Pointage de sortie enregistré avec succès !')
        
        return redirect('attendance:punch')
    
    def get_client_ip(self):
        """Récupère l'adresse IP du client."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class MyAttendanceView(EmployeeRequiredMixin, ListView):
    """Vue pour consulter ses propres pointages."""
    model = Attendance
    template_name = 'attendance/my_attendance.html'
    context_object_name = 'attendances'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtre les présences de l'utilisateur connecté."""
        queryset = Attendance.objects.filter(
            employee=self.request.user
        ).order_by('-date', '-time')
        
        # Filtres
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset


class PunchAPIView(EmployeeRequiredMixin, TemplateView):
    """API pour le pointage via AJAX."""
    
    def post(self, request, *args, **kwargs):
        """Traite le pointage via AJAX."""
        try:
            data = json.loads(request.body)
            user = request.user
            today = date.today()
            
            # Vérifier les permissions
            if not user.employee_profile.can_punch:
                return JsonResponse({'success': False, 'error': 'Non autorisé'})
            
            punch_type = data.get('punch_type')
            latitude = data.get('latitude', 0.0)
            longitude = data.get('longitude', 0.0)
            accuracy = data.get('accuracy', 0.0)
            
            # Vérifier les doublons
            existing_punch = Attendance.objects.filter(
                employee=user,
                date=today,
                punch_type=punch_type
            ).exists()
            
            if existing_punch:
                return JsonResponse({
                    'success': False, 
                    'error': f'Pointage {punch_type} déjà effectué aujourd\'hui'
                })
            
            # Créer le pointage
            attendance = Attendance.objects.create(
                employee=user,
                date=today,
                time=timezone.now().time(),
                punch_type=punch_type,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                source='web',
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Pointage {punch_type} enregistré',
                'attendance_id': attendance.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip