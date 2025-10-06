"""
Signaux pour le système de notifications.

Ce module contient les signaux Django pour :
- Déclencher automatiquement les notifications
- Intégrer avec les modèles existants
- Gérer les événements système

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from django.utils import timezone

from .models import NotificationSettings
from .services import NotificationService


@receiver(post_save, sender=User)
def create_notification_settings(sender, instance, created, **kwargs):
    """
    Crée automatiquement les paramètres de notifications pour un nouvel utilisateur.
    """
    if created:
        NotificationSettings.objects.get_or_create(user=instance)


@receiver(user_logged_in)
def send_welcome_notification(sender, request, user, **kwargs):
    """
    Envoie une notification de bienvenue à la première connexion.
    """
    # Vérifier si c'est la première connexion
    if user.last_login is None:
        NotificationService.create_notification(
            user=user,
            title="Bienvenue dans le système de gestion de présence !",
            message="Votre compte a été créé avec succès. Vous pouvez maintenant utiliser toutes les fonctionnalités du système.",
            notification_type='success',
            action_url='/dashboard/',
            action_text='Accéder au tableau de bord'
        )


# Signaux pour les congés
@receiver(post_save, sender='leave.LeaveRequest')
def handle_leave_request_notifications(sender, instance, created, **kwargs):
    """
    Gère les notifications pour les demandes de congés.
    """
    from leave.models import LeaveRequest
    
    if not isinstance(instance, LeaveRequest):
        return
    
    # Nouvelle demande créée
    if created:
        # Notifier le manager
        if instance.manager:
            NotificationService.create_notification(
                user=instance.manager,
                title="Nouvelle demande de congé à valider",
                message=f"{instance.employee.get_full_name()} a créé une nouvelle demande de congé du {instance.start_date} au {instance.end_date}.",
                notification_type='info',
                priority='high',
                action_url=f'/leave/approvals/{instance.id}/',
                action_text='Examiner la demande'
            )
            
            # Email au manager
            NotificationService.send_template_email(
                template_type='leave_request_created',
                recipient=instance.manager,
                context={
                    'employee': instance.employee,
                    'leave_request': instance,
                    'leave_type': instance.leave_type,
                    'start_date': instance.start_date,
                    'end_date': instance.end_date,
                    'duration': instance.duration_days,
                    'reason': instance.reason,
                }
            )
    
    # Demande modifiée (changement de statut)
    else:
        # Vérifier si le statut a changé
        if hasattr(instance, '_previous_status'):
            old_status = instance._previous_status
            new_status = instance.status
            
            if old_status != new_status:
                # Notifier selon le nouveau statut
                if new_status == 'approved_manager':
                    NotificationService.send_leave_notifications(instance, 'approved_manager')
                elif new_status == 'rejected_manager':
                    NotificationService.send_leave_notifications(instance, 'rejected_manager')
                elif new_status == 'approved_rh':
                    NotificationService.send_leave_notifications(instance, 'approved_rh')
                elif new_status == 'rejected_rh':
                    NotificationService.send_leave_notifications(instance, 'rejected_rh')


# Signal pour les anomalies de présence
@receiver(post_save, sender='attendance.AttendanceAnomaly')
def handle_attendance_anomaly_notifications(sender, instance, created, **kwargs):
    """
    Gère les notifications pour les anomalies de présence.
    """
    from attendance.models import AttendanceAnomaly
    
    if not isinstance(instance, AttendanceAnomaly):
        return
    
    if created:
        # Notifier l'employé et le manager
        NotificationService.send_attendance_anomaly_notification(instance)


# Signal pour les nouvelles présences (pointage)
@receiver(post_save, sender='attendance.Attendance')
def handle_attendance_notifications(sender, instance, created, **kwargs):
    """
    Gère les notifications pour les pointages.
    """
    from attendance.models import Attendance
    
    if not isinstance(instance, Attendance):
        return
    
    # Premier pointage de la journée
    if created and instance.punch_type == 'in':
        # Notifier le manager si c'est un pointage tardif
        if instance.time and instance.time.hour > 9:  # Après 9h
            if instance.employee.employee_profile.manager:
                NotificationService.create_notification(
                    user=instance.employee.employee_profile.manager,
                    title="Pointage tardif détecté",
                    message=f"{instance.employee.get_full_name()} a pointé à {instance.time.strftime('%H:%M')} ce matin.",
                    notification_type='warning',
                    action_url=f'/attendance/my-attendance/',
                    action_text='Voir la présence'
                )


# Signal pour les nouveaux utilisateurs créés par RH/DG
@receiver(post_save, sender='accounts.EmployeeProfile')
def handle_new_employee_notifications(sender, instance, created, **kwargs):
    """
    Gère les notifications pour les nouveaux employés.
    """
    if created:
        # Notification de bienvenue à l'employé
        NotificationService.create_notification(
            user=instance.user,
            title="Votre compte a été créé",
            message=f"Bienvenue ! Votre compte employé a été créé avec succès. Votre rôle : {instance.get_role_display()}.",
            notification_type='success',
            action_url='/dashboard/',
            action_text='Accéder au système'
        )
        
        # Email de bienvenue
        NotificationService.send_template_email(
            template_type='welcome',
            recipient=instance.user,
            context={
                'employee': instance.user,
                'role': instance.get_role_display(),
                'department': instance.department.name if instance.department else 'Non assigné',
            }
        )


# Fonction utilitaire pour préserver l'ancien statut
def preserve_leave_request_status(sender, instance, **kwargs):
    """
    Préserve l'ancien statut d'une demande de congé avant sauvegarde.
    """
    if hasattr(instance, 'id') and instance.id:
        try:
            old_instance = sender.objects.get(id=instance.id)
            instance._previous_status = old_instance.status
        except sender.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


# Connecter le signal pour préserver le statut
post_save.connect(preserve_leave_request_status, sender='leave.LeaveRequest')
