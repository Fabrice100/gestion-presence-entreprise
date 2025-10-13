"""
Service de notifications pour PresencePro.

Ce module gère l'envoi de notifications par email pour :
- Création de compte
- Validation/rejet de congés
- Alertes importantes
- Rappels
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class NotificationService:
    """Service centralisé pour l'envoi de notifications."""
    
    @staticmethod
    def send_welcome_email(user, employee_id, temporary_password):
        """
        Envoie un email de bienvenue avec les credentials.
        
        Args:
            user: Utilisateur Django
            employee_id: ID employé généré
            temporary_password: Mot de passe temporaire
        
        Returns:
            bool: True si succès, False sinon
        """
        try:
            subject = f'{settings.SITE_NAME} - Bienvenue ! Vos accès'
            
            context = {
                'user': user,
                'employee_id': employee_id,
                'temporary_password': temporary_password,
                'login_url': f'{settings.SITE_URL}/accounts/login/',
                'site_name': settings.SITE_NAME,
            }
            
            html_message = render_to_string('accounts/welcome_email.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            print(f"✅ Email de bienvenue envoyé à {user.email}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur envoi email: {str(e)}")
            return False
    
    @staticmethod
    def send_leave_approved_notification(leave_request, approved_by):
        """
        Notifie l'employé que sa demande de congé est approuvée.
        
        Args:
            leave_request: Demande de congé
            approved_by: Utilisateur qui a approuvé
        """
        try:
            subject = f'{settings.SITE_NAME} - Demande de congé approuvée'
            
            message = f"""
Bonjour {leave_request.employee.get_full_name()},

Bonne nouvelle ! Votre demande de congé a été approuvée.

Détails :
- Type : {leave_request.leave_type.name}
- Période : {leave_request.start_date.strftime('%d/%m/%Y')} - {leave_request.end_date.strftime('%d/%m/%Y')}
- Durée : {leave_request.duration_days} jour(s)
- Approuvé par : {approved_by.get_full_name()}

Vous pouvez consulter les détails sur {settings.SITE_URL}

Cordialement,
L'équipe {settings.SITE_NAME}
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[leave_request.employee.email],
                fail_silently=False,
            )
            
            print(f"✅ Notification d'approbation envoyée à {leave_request.employee.email}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur notification: {str(e)}")
            return False
    
    @staticmethod
    def send_leave_rejected_notification(leave_request, rejected_by, comment):
        """
        Notifie l'employé que sa demande de congé est rejetée.
        
        Args:
            leave_request: Demande de congé
            rejected_by: Utilisateur qui a rejeté
            comment: Commentaire du rejet
        """
        try:
            subject = f'{settings.SITE_NAME} - Demande de congé rejetée'
            
            message = f"""
Bonjour {leave_request.employee.get_full_name()},

Votre demande de congé a été rejetée.

Détails :
- Type : {leave_request.leave_type.name}
- Période : {leave_request.start_date.strftime('%d/%m/%Y')} - {leave_request.end_date.strftime('%d/%m/%Y')}
- Durée : {leave_request.duration_days} jour(s)
- Rejeté par : {rejected_by.get_full_name()}

Motif du rejet :
{comment}

Vous pouvez soumettre une nouvelle demande si nécessaire.

Cordialement,
L'équipe {settings.SITE_NAME}
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[leave_request.employee.email],
                fail_silently=False,
            )
            
            print(f"✅ Notification de rejet envoyée à {leave_request.employee.email}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur notification: {str(e)}")
            return False
    
    @staticmethod
    def send_leave_pending_notification(leave_request, validator):
        """
        Notifie le validateur qu'une nouvelle demande attend sa validation.
        
        Args:
            leave_request: Demande de congé
            validator: Utilisateur qui doit valider (manager ou RH)
        """
        try:
            subject = f'{settings.SITE_NAME} - Nouvelle demande de congé à valider'
            
            message = f"""
Bonjour {validator.get_full_name()},

Une nouvelle demande de congé nécessite votre validation.

Employé : {leave_request.employee.get_full_name()}
Type : {leave_request.leave_type.name}
Période : {leave_request.start_date.strftime('%d/%m/%Y')} - {leave_request.end_date.strftime('%d/%m/%Y')}
Durée : {leave_request.duration_days} jour(s)

Motif : {leave_request.reason}

Validez cette demande sur : {settings.SITE_URL}/leave/approvals/{leave_request.pk}/

Cordialement,
L'équipe {settings.SITE_NAME}
"""
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[validator.email],
                fail_silently=False,
            )
            
            print(f"✅ Notification envoyée au validateur {validator.email}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur notification: {str(e)}")
            return False



