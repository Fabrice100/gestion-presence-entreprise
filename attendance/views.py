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
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import date, timedelta
import json
import csv
from django.http import HttpResponse

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


# ============================================================================
# VUES RH - GESTION DES ANOMALIES
# ============================================================================

def is_hr_staff(user):
    """Vérifie si l'utilisateur est membre du groupe RH."""
    return user.is_authenticated and (user.groups.filter(name='RH').exists() or user.is_superuser)


@login_required
@user_passes_test(is_hr_staff, login_url='/accounts/login/')
def rh_anomalies_list(request):
    """
    Vue liste des anomalies de pointage pour le personnel RH.
    
    Affiche uniquement les oublis de sortie (missing_punch_out) en attente.
    Permet filtrage par date et employé.
    """
    # Récupérer les paramètres de filtrage
    date_filter = request.GET.get('date', '')
    employee_filter = request.GET.get('employee', '')
    
    # Requête de base : anomalies missing_punch_out en attente
    anomalies = AttendanceAnomaly.objects.filter(
        anomaly_type='missing_punch_out',
        status='pending'
    ).select_related('attendance', 'attendance__employee', 'attendance__employee__user').order_by('-detected_at')
    
    # Appliquer les filtres
    if date_filter:
        anomalies = anomalies.filter(attendance__date=date_filter)
    
    if employee_filter:
        anomalies = anomalies.filter(
            Q(attendance__employee__user__first_name__icontains=employee_filter) |
            Q(attendance__employee__user__last_name__icontains=employee_filter) |
            Q(attendance__employee__user__username__icontains=employee_filter)
        )
    
    # Statistiques
    total_anomalies = anomalies.count()
    
    context = {
        'anomalies': anomalies,
        'total_anomalies': total_anomalies,
        'date_filter': date_filter,
        'employee_filter': employee_filter,
    }
    
    return render(request, 'attendance/rh_anomalies.html', context)


@login_required
@user_passes_test(is_hr_staff, login_url='/accounts/login/')
def rh_anomaly_correct(request, anomaly_id):
    """
    Vue de correction d'une anomalie de pointage par RH.
    
    Permet au personnel RH de saisir les heures travaillées manuellement
    pour corriger un oubli de sortie.
    """
    from .forms import AnomalyCorrectForm
    
    anomaly = get_object_or_404(AttendanceAnomaly, id=anomaly_id, anomaly_type='missing_punch_out')
    attendance = anomaly.attendance
    
    if request.method == 'POST':
        form = AnomalyCorrectForm(request.POST)
        if form.is_valid():
            worked_hours = form.cleaned_data['worked_hours']
            comment = form.cleaned_data.get('comment', '')
            
            # Mettre à jour les heures travaillées
            attendance.worked_hours = worked_hours
            attendance.save()
            
            # Marquer l'anomalie comme résolue
            anomaly.status = 'resolved'
            anomaly.resolved_by = request.user
            anomaly.resolved_at = timezone.now()
            anomaly.resolution_note = f"Correction RH: {worked_hours}h travaillées. {comment}".strip()
            anomaly.save()
            
            messages.success(
                request,
                f"Anomalie corrigée avec succès. {attendance.employee.user.get_full_name()} - {attendance.date}: {worked_hours}h"
            )
            return redirect('attendance:rh_anomalies_list')
    else:
        form = AnomalyCorrectForm()
    
    context = {
        'form': form,
        'anomaly': anomaly,
        'attendance': attendance,
        'employee': attendance.employee,
    }
    
    return render(request, 'attendance/rh_anomaly_correct.html', context)


@login_required
@user_passes_test(is_hr_staff, login_url='/accounts/login/')
def rh_anomaly_ignore(request, anomaly_id):
    """
    Ignorer une anomalie (marquée comme résolue sans correction).
    
    Utilisé quand l'anomalie est légitime (ex: employé absent, congé non déclaré).
    """
    anomaly = get_object_or_404(AttendanceAnomaly, id=anomaly_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Ignorée par RH')
        
        anomaly.status = 'ignored'
        anomaly.resolved_by = request.user
        anomaly.resolved_at = timezone.now()
        anomaly.resolution_note = f"Ignorée: {reason}"
        anomaly.save()
        
        messages.info(request, f"Anomalie ignorée: {anomaly.attendance.employee.user.get_full_name()} - {anomaly.attendance.date}")
        return redirect('attendance:rh_anomalies_list')
    
    return redirect('attendance:rh_anomalies_list')


@login_required
@user_passes_test(is_hr_staff, login_url='/accounts/login/')
def rh_anomalies_export_csv(request):
    """
    Export CSV des anomalies affichées (filtres appliqués).
    Accessible uniquement au personnel RH.
    """
    # Récupérer les mêmes filtres que la liste
    date_filter = request.GET.get('date', '')
    employee_filter = request.GET.get('employee', '')

    anomalies = AttendanceAnomaly.objects.filter(
        anomaly_type='missing_punch_out',
        status='pending'
    ).select_related('attendance', 'attendance__employee', 'attendance__employee__user').order_by('-detected_at')

    if date_filter:
        anomalies = anomalies.filter(attendance__date=date_filter)

    if employee_filter:
        anomalies = anomalies.filter(
            Q(attendance__employee__user__first_name__icontains=employee_filter) |
            Q(attendance__employee__user__last_name__icontains=employee_filter) |
            Q(attendance__employee__user__username__icontains=employee_filter)
        )

    # Préparer la réponse CSV
    response = HttpResponse(content_type='text/csv')
    filename = f"anomalies_missing_punch_out_{date.today().isoformat()}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    # Entêtes
    writer.writerow(['employee_username', 'employee_full_name', 'date', 'entry_time', 'detected_at', 'description'])

    for a in anomalies:
        emp_user = a.attendance.employee
        # emp_user may be a User or EmployeeProfile; try to extract username and full name
        if hasattr(emp_user, 'user'):
            user_obj = emp_user.user
        else:
            user_obj = emp_user

        username = getattr(user_obj, 'username', '')
        full_name = getattr(user_obj, 'get_full_name', lambda: '')() if hasattr(user_obj, 'get_full_name') else ''
        entry_time = a.attendance.time.strftime('%H:%M') if a.attendance.time else ''
        detected = a.detected_at.strftime('%Y-%m-%d %H:%M') if a.detected_at else ''
        writer.writerow([username, full_name, a.attendance.date.isoformat(), entry_time, detected, a.description or ''])

    return response
