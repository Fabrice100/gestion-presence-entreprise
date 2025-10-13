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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import date, timedelta
import json

from .models import Attendance, AttendanceAnomaly


class LoginRequiredMixin:
    """Mixin pour exiger une authentification."""
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class PunchView(LoginRequiredMixin, TemplateView):
    """Vue principale pour le pointage."""
    template_name = 'attendance/punch.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        
        # Vérifier si l'utilisateur peut pointer
        if not user.employee_profile.can_punch:
            messages.error(self.request, 'Vous n\'êtes pas autorisé à pointer.')
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
        """Traite le pointage via POST avec validation GPS et règles métier."""
        from math import radians, sin, cos, sqrt, atan2
        from datetime import datetime, time as dt_time
        from .admin_models import CompanySettings
        
        user = request.user
        today = date.today()
        now = timezone.now()
        current_time = now.time()
        
        # Charger la configuration
        settings = CompanySettings.load()
        
        # Vérifier les permissions
        if not user.employee_profile.can_punch:
            messages.error(request, 'Vous n\'êtes pas autorisé à pointer.')
            return redirect('dashboard:dashboard')
        
        punch_type = request.POST.get('punch_type')
        latitude_str = request.POST.get('latitude', '')
        longitude_str = request.POST.get('longitude', '')
        accuracy_str = request.POST.get('accuracy', '')
        
        # === VALIDATION GPS OBLIGATOIRE ===
        if not latitude_str or not longitude_str or latitude_str == '0.0':
            messages.error(
                request,
                '🚫 Géolocalisation requise ! Veuillez activer le GPS et autoriser la localisation.'
            )
            return redirect('attendance:punch')
        
        try:
            latitude = float(latitude_str)
            longitude = float(longitude_str)
            accuracy = float(accuracy_str) if accuracy_str else 999.0
        except ValueError:
            messages.error(request, '❌ Données GPS invalides.')
            return redirect('attendance:punch')
        
        # === VALIDATION PRÉCISION GPS ===
        if accuracy > settings.gps_accuracy_max_meters:
            messages.warning(
                request,
                f'⚠️  Précision GPS insuffisante ({accuracy:.0f}m). Essayez à l\'extérieur ou près d\'une fenêtre.'
            )
            return redirect('attendance:punch')
        
        # === CALCUL DISTANCE DU BUREAU (Formule Haversine) ===
        def calculate_distance(lat1, lon1, lat2, lon2):
            """Calcule la distance entre deux coordonnées GPS en mètres."""
            R = 6371000  # Rayon de la Terre en mètres
            
            lat1_rad = radians(lat1)
            lat2_rad = radians(lat2)
            delta_lat = radians(lat2 - lat1)
            delta_lon = radians(lon2 - lon1)
            
            a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            
            return R * c
        
        distance = calculate_distance(
            latitude, longitude,
            settings.site_center_latitude, settings.site_center_longitude
        )
        
        # === VALIDATION ZONE AUTORISÉE ===
        if distance > settings.allowed_radius_meters:
            messages.error(
                request,
                f'🚫 Vous êtes trop loin du bureau ({distance:.0f}m). '
                f'Vous devez être à moins de {settings.allowed_radius_meters}m pour pointer.'
            )
            return redirect('attendance:punch')
        
        # === VÉRIFICATION DOUBLONS ===
        existing_punch = Attendance.objects.filter(
            employee=user,
            date=today,
            punch_type=punch_type
        ).exists()
        
        if existing_punch:
            messages.error(
                request,
                f'❌ Pointage {"d\'entrée" if punch_type == "in" else "de sortie"} déjà effectué aujourd\'hui.'
            )
            return redirect('attendance:punch')
        
        # === DÉTECTION STATUT (retard, normal, etc.) ===
        status = 'normal'
        warning_message = ''
        
        if punch_type == 'in':
            # Utiliser les horaires de la configuration
            work_start = settings.work_start_time
            late_threshold = datetime.combine(today, work_start) + timedelta(minutes=settings.late_tolerance_minutes)
            late_threshold_time = late_threshold.time()
            
            if current_time > late_threshold_time:
                status = 'late'
                minutes_late = (datetime.combine(today, current_time) - datetime.combine(today, work_start)).seconds // 60
                warning_message = f'⚠️  Retard de {minutes_late} minutes détecté.'
        
        elif punch_type == 'out':
            work_end = settings.work_end_time
            if current_time < work_end:
                status = 'early'
                warning_message = '⚠️  Sortie anticipée détectée.'
        
        try:
            # Créer le pointage
            attendance = Attendance.objects.create(
                employee=user,
                date=today,
                time=current_time,
                punch_type=punch_type,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                distance_from_site=distance,
                status=status,
                source='web',
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request)
            )
            
            # Message de succès
            if warning_message:
                messages.warning(request, warning_message)
            
            messages.success(
                request,
                f'Pointage {"d\'entrée" if punch_type == "in" else "de sortie"} enregistré à {current_time.strftime("%H:%M")}'
            )
            
        except Exception as e:
            messages.error(request, f'❌ Erreur lors du pointage : {str(e)}')
        
        return redirect('attendance:punch')
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PunchInView(LoginRequiredMixin, CreateView):
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


class PunchOutView(LoginRequiredMixin, CreateView):
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


class MyAttendanceView(LoginRequiredMixin, ListView):
    """Vue pour consulter ses propres présences."""
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


class PunchAPIView(LoginRequiredMixin, TemplateView):
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