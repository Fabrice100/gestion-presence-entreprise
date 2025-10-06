"""
Services pour le système de notifications.

Ce module contient les services pour :
- Envoi d'emails automatiques
- Création de notifications
- Gestion des templates
- Rappels et alertes

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Notification, EmailTemplate, NotificationSettings


logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service principal pour la gestion des notifications.
    """
    
    @staticmethod
    def create_notification(
        user,
        title,
        message,
        notification_type='info',
        priority='normal',
        action_url=None,
        action_text=None,
        send_email=True
    ):
        """
        Crée une notification pour un utilisateur.
        """
        # Créer la notification
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url,
            action_text=action_text
        )
        
        # Envoyer par email si demandé
        if send_email:
            notification.send_email()
        
        return notification
    
    @staticmethod
    def send_template_email(template_type, recipient, context=None, extra_recipients=None):
        """
        Envoie un email en utilisant un template.
        """
        try:
            # Récupérer le template
            template = EmailTemplate.objects.get(
                template_type=template_type,
                is_active=True
            )
            
            # Préparer le contexte
            if context is None:
                context = {}
            
            # Ajouter des informations système
            context.update({
                'site_name': getattr(settings, 'SITE_NAME', 'Système de Gestion de Présence'),
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
                'current_year': timezone.now().year,
            })
            
            # Rendre le template
            rendered = template.render(context)
            
            # Préparer les destinataires
            recipients = [recipient.email] if hasattr(recipient, 'email') else [recipient]
            if extra_recipients:
                recipients.extend(extra_recipients)
            
            # Envoyer l'email
            email = EmailMultiAlternatives(
                subject=rendered['subject'],
                body=rendered['text_content'],
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients
            )
            email.attach_alternative(rendered['html_content'], "text/html")
            email.send()
            
            logger.info(f"Email envoyé: {template_type} à {recipients}")
            return True
            
        except EmailTemplate.DoesNotExist:
            logger.error(f"Template non trouvé: {template_type}")
            return False
        except Exception as e:
            logger.error(f"Erreur envoi email {template_type}: {e}")
            return False
    
    @staticmethod
    def send_leave_notifications(leave_request, action_type):
        """
        Envoie les notifications liées aux congés.
        """
        template_type = f'leave_request_{action_type}'
        
        # Contexte pour les templates
        context = {
            'employee': leave_request.employee,
            'leave_request': leave_request,
            'leave_type': leave_request.leave_type,
            'start_date': leave_request.start_date,
            'end_date': leave_request.end_date,
            'duration': leave_request.duration_days,
            'reason': leave_request.reason,
        }
        
        if action_type in ['approved_manager', 'rejected_manager']:
            # Notification pour l'employé
            NotificationService.send_template_email(
                template_type=template_type,
                recipient=leave_request.employee,
                context=context
            )
            
            # Créer une notification système
            title = f"Demande de congé {action_type.replace('_', ' ').title()}"
            message = f"Votre demande de congé du {leave_request.start_date} au {leave_request.end_date} a été {action_type.split('_')[0]}."
            
            NotificationService.create_notification(
                user=leave_request.employee,
                title=title,
                message=message,
                notification_type='success' if 'approved' in action_type else 'warning',
                action_url=f'/leave/requests/',
                action_text='Voir mes demandes'
            )
        
        elif action_type in ['approved_rh', 'rejected_rh']:
            # Notification pour l'employé
            NotificationService.send_template_email(
                template_type=template_type,
                recipient=leave_request.employee,
                context=context
            )
            
            # Notification pour le manager si différent
            if leave_request.manager and leave_request.manager != leave_request.employee:
                NotificationService.send_template_email(
                    template_type=template_type,
                    recipient=leave_request.manager,
                    context=context
                )
            
            # Créer une notification système
            title = f"Demande de congé {action_type.replace('_', ' ').title()}"
            message = f"Votre demande de congé du {leave_request.start_date} au {leave_request.end_date} a été {action_type.split('_')[0]} par les RH/DG."
            
            NotificationService.create_notification(
                user=leave_request.employee,
                title=title,
                message=message,
                notification_type='success' if 'approved' in action_type else 'error',
                action_url=f'/leave/requests/',
                action_text='Voir mes demandes'
            )
    
    @staticmethod
    def send_attendance_anomaly_notification(anomaly):
        """
        Envoie une notification pour une anomalie de présence.
        """
        context = {
            'employee': anomaly.attendance.employee,
            'anomaly': anomaly,
            'attendance': anomaly.attendance,
            'anomaly_type': anomaly.anomaly_type,
            'description': anomaly.description,
            'date': anomaly.attendance.date,
            'time': anomaly.attendance.time,
        }
        
        # Email à l'employé
        NotificationService.send_template_email(
            template_type='attendance_anomaly',
            recipient=anomaly.attendance.employee,
            context=context
        )
        
        # Email au manager
        if anomaly.attendance.employee.employee_profile.manager:
            NotificationService.send_template_email(
                template_type='attendance_anomaly',
                recipient=anomaly.attendance.employee.employee_profile.manager,
                context=context
            )
        
        # Notification système
        title = "Anomalie de présence détectée"
        message = f"Une anomalie de présence a été détectée le {anomaly.attendance.date} à {anomaly.attendance.time}: {anomaly.description}"
        
        NotificationService.create_notification(
            user=anomaly.attendance.employee,
            title=title,
            message=message,
            notification_type='warning',
            priority='high',
            action_url=f'/attendance/my-attendance/',
            action_text='Voir ma présence'
        )
    
    @staticmethod
    def send_leave_reminders():
        """
        Envoie des rappels pour les congés à venir.
        """
        from leave.models import LeaveRequest
        
        # Congés qui commencent dans 3 jours
        reminder_date = timezone.now().date() + timedelta(days=3)
        
        upcoming_leaves = LeaveRequest.objects.filter(
            status='approved_rh',
            start_date=reminder_date
        )
        
        for leave_request in upcoming_leaves:
            context = {
                'employee': leave_request.employee,
                'leave_request': leave_request,
                'start_date': leave_request.start_date,
                'days_until': 3,
            }
            
            # Email de rappel
            NotificationService.send_template_email(
                template_type='leave_reminder',
                recipient=leave_request.employee,
                context=context
            )
            
            # Notification système
            title = "Rappel de congé"
            message = f"Votre congé commence dans 3 jours (le {leave_request.start_date})"
            
            NotificationService.create_notification(
                user=leave_request.employee,
                title=title,
                message=message,
                notification_type='info',
                action_url=f'/leave/requests/',
                action_text='Voir mes demandes'
            )
    
    @staticmethod
    def mark_all_as_read(user):
        """
        Marque toutes les notifications comme lues pour un utilisateur.
        """
        Notification.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
    
    @staticmethod
    def get_unread_count(user):
        """
        Retourne le nombre de notifications non lues pour un utilisateur.
        """
        return Notification.objects.filter(
            user=user,
            is_read=False
        ).count()
    
    @staticmethod
    def cleanup_old_notifications(days=30):
        """
        Supprime les anciennes notifications lues.
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        
        deleted_count = Notification.objects.filter(
            is_read=True,
            read_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Supprimé {deleted_count} anciennes notifications")
        return deleted_count


class EmailTemplateService:
    """
    Service pour la gestion des templates d'emails.
    """
    
    @staticmethod
    def create_default_templates():
        """
        Crée les templates d'emails par défaut.
        """
        templates_data = [
            {
                'name': 'Demande de congé créée',
                'template_type': 'leave_request_created',
                'subject': 'Nouvelle demande de congé - {employee.get_full_name}',
                'html_content': '''
                <h2>Nouvelle demande de congé</h2>
                <p>Bonjour {employee.get_full_name},</p>
                <p>Votre demande de congé a été créée avec succès :</p>
                <ul>
                    <li><strong>Type :</strong> {leave_type.name}</li>
                    <li><strong>Période :</strong> Du {start_date} au {end_date}</li>
                    <li><strong>Durée :</strong> {duration} jour(s)</li>
                    <li><strong>Motif :</strong> {reason}</li>
                </ul>
                <p>Votre demande sera examinée par votre manager.</p>
                <p>Vous recevrez une notification dès qu'une décision sera prise.</p>
                ''',
            },
            {
                'name': 'Congé approuvé par manager',
                'template_type': 'leave_request_approved_manager',
                'subject': 'Demande de congé approuvée par votre manager',
                'html_content': '''
                <h2>Demande de congé approuvée</h2>
                <p>Bonjour {employee.get_full_name},</p>
                <p>Votre demande de congé a été approuvée par votre manager :</p>
                <ul>
                    <li><strong>Type :</strong> {leave_type.name}</li>
                    <li><strong>Période :</strong> Du {start_date} au {end_date}</li>
                    <li><strong>Durée :</strong> {duration} jour(s)</li>
                </ul>
                <p>Votre demande est maintenant transmise aux RH/DG pour validation finale.</p>
                ''',
            },
            {
                'name': 'Congé rejeté par manager',
                'template_type': 'leave_request_rejected_manager',
                'subject': 'Demande de congé rejetée par votre manager',
                'html_content': '''
                <h2>Demande de congé rejetée</h2>
                <p>Bonjour {employee.get_full_name},</p>
                <p>Votre demande de congé a été rejetée par votre manager :</p>
                <ul>
                    <li><strong>Type :</strong> {leave_type.name}</li>
                    <li><strong>Période :</strong> Du {start_date} au {end_date}</li>
                    <li><strong>Durée :</strong> {duration} jour(s)</li>
                </ul>
                <p>Vous pouvez contacter votre manager pour plus d'informations.</p>
                ''',
            },
            {
                'name': 'Congé approuvé définitivement',
                'template_type': 'leave_request_approved_rh',
                'subject': 'Demande de congé approuvée définitivement',
                'html_content': '''
                <h2>Demande de congé approuvée</h2>
                <p>Bonjour {employee.get_full_name},</p>
                <p>Votre demande de congé a été approuvée définitivement :</p>
                <ul>
                    <li><strong>Type :</strong> {leave_type.name}</li>
                    <li><strong>Période :</strong> Du {start_date} au {end_date}</li>
                    <li><strong>Durée :</strong> {duration} jour(s)</li>
                </ul>
                <p>Votre congé est confirmé. Bonnes vacances !</p>
                ''',
            },
            {
                'name': 'Congé rejeté définitivement',
                'template_type': 'leave_request_rejected_rh',
                'subject': 'Demande de congé rejetée définitivement',
                'html_content': '''
                <h2>Demande de congé rejetée</h2>
                <p>Bonjour {employee.get_full_name},</p>
                <p>Votre demande de congé a été rejetée définitivement :</p>
                <ul>
                    <li><strong>Type :</strong> {leave_type.name}</li>
                    <li><strong>Période :</strong> Du {start_date} au {end_date}</li>
                    <li><strong>Durée :</strong> {duration} jour(s)</li>
                </ul>
                <p>Vous pouvez contacter les RH/DG pour plus d'informations.</p>
                ''',
            },
            {
                'name': 'Rappel de congé',
                'template_type': 'leave_reminder',
                'subject': 'Rappel : Votre congé commence dans {days_until} jour(s)',
                'html_content': '''
                <h2>Rappel de congé</h2>
                <p>Bonjour {employee.get_full_name},</p>
                <p>Ceci est un rappel que votre congé commence dans {days_until} jour(s) :</p>
                <ul>
                    <li><strong>Date de début :</strong> {start_date}</li>
                </ul>
                <p>Assurez-vous d'avoir terminé vos tâches en cours.</p>
                ''',
            },
            {
                'name': 'Anomalie de présence',
                'template_type': 'attendance_anomaly',
                'subject': 'Anomalie de présence détectée',
                'html_content': '''
                <h2>Anomalie de présence</h2>
                <p>Bonjour {employee.get_full_name},</p>
                <p>Une anomalie de présence a été détectée :</p>
                <ul>
                    <li><strong>Date :</strong> {date}</li>
                    <li><strong>Heure :</strong> {time}</li>
                    <li><strong>Type :</strong> {anomaly_type}</li>
                    <li><strong>Description :</strong> {description}</li>
                </ul>
                <p>Veuillez contacter votre manager si nécessaire.</p>
                ''',
            },
        ]
        
        created_count = 0
        for template_data in templates_data:
            template, created = EmailTemplate.objects.get_or_create(
                template_type=template_data['template_type'],
                defaults=template_data
            )
            if created:
                created_count += 1
        
        return created_count
