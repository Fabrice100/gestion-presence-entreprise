"""
Service de notifications pour PresencePro.

Ce module gère l'envoi de notifications par email pour :
- Création de compte
- Validation/rejet de congés
- Alertes importantes
- Rappels
"""

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


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
            
            logger.info(f"Email de bienvenue envoyé à {user.email}", extra={
                'user_id': user.id,
                'email': user.email,
                'employee_id': employee_id
            })
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {str(e)}", exc_info=True, extra={
                'user_id': user.id if user else None,
                'email': user.email if user else None
            })
            return False
    
    @staticmethod
    def send_leave_approved_notification(leave_request, approved_by):
        """
        Notifie l'employé que sa demande de congé est approuvée.
        
        Args:
            leave_request: Demande de congé
            approved_by: Utilisateur qui a approuvé (manager ou RH)
        """
        try:
            from accounts.models import EmployeeProfile
            from leave.leave_balance_service import leave_balance_service
            
            # Déterminer le niveau de validation
            approver_role = approved_by.employee_profile.role if hasattr(approved_by, 'employee_profile') else None
            is_final_approval = (leave_request.status == 'approved_rh')
            is_manager_approval = (leave_request.status == 'approved_manager')
            
            # Construire le sujet selon le niveau
            if is_final_approval:
                subject = f'{settings.SITE_NAME} - ✅ Demande de congé définitivement approuvée'
                approval_status = "DÉFINITIVEMENT APPROUVÉE"
                next_step = ""
            elif is_manager_approval:
                subject = f'{settings.SITE_NAME} - ✅ Demande de congé validée par votre manager'
                approval_status = "VALIDÉE PAR VOTRE MANAGER"
                next_step = "\n⚠️ IMPORTANT : Votre demande nécessite encore la validation finale des Ressources Humaines. Vous recevrez une notification une fois la validation RH effectuée."
            else:
                subject = f'{settings.SITE_NAME} - ✅ Demande de congé approuvée'
                approval_status = "APPROUVÉE"
                next_step = ""
            
            # Récupérer le commentaire si disponible
            comment = ""
            if is_manager_approval and leave_request.manager_comment:
                comment = f"\nCommentaire du manager :\n{leave_request.manager_comment}\n"
            elif is_final_approval and leave_request.rh_comment:
                comment = f"\nCommentaire des Ressources Humaines :\n{leave_request.rh_comment}\n"
            
            # Récupérer le solde restant pour les approbations finales
            balance_info = ""
            if is_final_approval and leave_request.leave_type.deducts_balance:
                try:
                    remaining = leave_balance_service.get_remaining_balance(leave_request.employee)
                    taken = leave_balance_service.get_taken_balance(leave_request.employee)
                    balance_info = f"""
Solde de congés :
- Solde utilisé : {taken} jour(s)
- Solde restant : {remaining} jour(s)
"""
                except Exception:
                    pass
            
            # URL de consultation
            detail_url = f"{settings.SITE_URL}/leave/requests/{leave_request.pk}/"
            
            message = f"""
Bonjour {leave_request.employee.get_full_name()},

═══════════════════════════════════════════════════════════
{approval_status}
═══════════════════════════════════════════════════════════

Bonne nouvelle ! Votre demande de congé a été approuvée.

📋 DÉTAILS DE LA DEMANDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type de congé : {leave_request.leave_type.name}
Période : Du {leave_request.start_date.strftime('%d/%m/%Y')} au {leave_request.end_date.strftime('%d/%m/%Y')}
Durée : {leave_request.duration_days} jour(s)
{comment}{balance_info}
👤 VALIDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Approuvé par : {approved_by.get_full_name()} ({'Ressources Humaines' if is_final_approval else 'Votre Manager'})
Date : {leave_request.rh_decision_at.strftime('%d/%m/%Y à %H:%M') if is_final_approval and leave_request.rh_decision_at else (leave_request.manager_decision_at.strftime('%d/%m/%Y à %H:%M') if leave_request.manager_decision_at else 'Non disponible')}
{next_step}
🔗 CONSULTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vous pouvez consulter les détails complets de votre demande en suivant ce lien :
{detail_url}

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
            
            logger.info(f"Notification d'approbation envoyée à {leave_request.employee.email}", extra={
                'leave_request_id': leave_request.id,
                'employee_id': leave_request.employee.id,
                'status': leave_request.status,
                'approved_by': approved_by.id if approved_by else None
            })
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification d'approbation: {str(e)}", exc_info=True, extra={
                'leave_request_id': leave_request.id if leave_request else None,
                'approved_by': approved_by.id if approved_by else None
            })
            return False
    
    @staticmethod
    def send_leave_rejected_notification(leave_request, rejected_by, comment):
        """
        Notifie l'employé que sa demande de congé est rejetée.
        
        Args:
            leave_request: Demande de congé
            rejected_by: Utilisateur qui a rejeté (manager ou RH)
            comment: Commentaire du rejet (obligatoire)
        """
        try:
            # Déterminer le niveau de rejet
            is_final_rejection = (leave_request.status == 'rejected_rh')
            is_manager_rejection = (leave_request.status == 'rejected_manager')
            
            if is_final_rejection:
                subject = f'{settings.SITE_NAME} - ❌ Demande de congé rejetée (décision finale RH)'
                rejection_level = "REJETÉE PAR LES RESSOURCES HUMAINES"
            elif is_manager_rejection:
                subject = f'{settings.SITE_NAME} - ❌ Demande de congé rejetée par votre manager'
                rejection_level = "REJETÉE PAR VOTRE MANAGER"
            else:
                subject = f'{settings.SITE_NAME} - ❌ Demande de congé rejetée'
                rejection_level = "REJETÉE"
            
            # S'assurer que le commentaire n'est pas vide
            if not comment or not comment.strip():
                comment = "Aucun motif spécifié."
            
            # Date du rejet
            rejection_date = ""
            if is_final_rejection and leave_request.rh_decision_at:
                rejection_date = leave_request.rh_decision_at.strftime('%d/%m/%Y à %H:%M')
            elif is_manager_rejection and leave_request.manager_decision_at:
                rejection_date = leave_request.manager_decision_at.strftime('%d/%m/%Y à %H:%M')
            
            # URL de consultation
            detail_url = f"{settings.SITE_URL}/leave/requests/{leave_request.pk}/"
            new_request_url = f"{settings.SITE_URL}/leave/requests/create/"
            
            message = f"""
Bonjour {leave_request.employee.get_full_name()},

═══════════════════════════════════════════════════════════
❌ {rejection_level}
═══════════════════════════════════════════════════════════

Nous regrettons de vous informer que votre demande de congé a été rejetée.

📋 DÉTAILS DE LA DEMANDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type de congé : {leave_request.leave_type.name}
Période demandée : Du {leave_request.start_date.strftime('%d/%m/%Y')} au {leave_request.end_date.strftime('%d/%m/%Y')}
Durée : {leave_request.duration_days} jour(s)
{"Motif de la demande : " + leave_request.reason if leave_request.reason else ""}

👤 DÉCISION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rejeté par : {rejected_by.get_full_name()} ({'Ressources Humaines' if is_final_rejection else 'Votre Manager'})
Date : {rejection_date if rejection_date else 'Non disponible'}

📝 MOTIF DU REJET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{comment}

💡 PROCHAINES ÉTAPES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vous pouvez :
• Consulter les détails de votre demande : {detail_url}
• Soumettre une nouvelle demande de congé si nécessaire : {new_request_url}
• Contacter les Ressources Humaines pour plus d'informations

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
            
            logger.info(f"Notification de rejet envoyée à {leave_request.employee.email}", extra={
                'leave_request_id': leave_request.id,
                'employee_id': leave_request.employee.id,
                'status': leave_request.status,
                'rejected_by': rejected_by.id if rejected_by else None
            })
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification de rejet: {str(e)}", exc_info=True, extra={
                'leave_request_id': leave_request.id if leave_request else None,
                'rejected_by': rejected_by.id if rejected_by else None
            })
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
            from accounts.models import EmployeeProfile
            from leave.leave_balance_service import leave_balance_service
            
            # Déterminer le type de validation
            validator_role = validator.employee_profile.role if hasattr(validator, 'employee_profile') else None
            
            if validator_role == 'rh':
                subject = f'{settings.SITE_NAME} - ⏳ Nouvelle demande de congé à valider (validation finale RH)'
                validation_type = "VALIDATION FINALE DES RESSOURCES HUMAINES"
                context_info = ""
                if leave_request.manager_decision == 'approved_manager' and leave_request.manager:
                    context_info = f"""
💼 VALIDATION PRÉCÉDENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cette demande a été validée par le manager : {leave_request.manager.get_full_name()}
{"Commentaire du manager : " + leave_request.manager_comment if leave_request.manager_comment else ""}
"""
            else:
                subject = f'{settings.SITE_NAME} - ⏳ Nouvelle demande de congé à valider'
                validation_type = "VALIDATION MANAGER (1ÈRE ÉTAPE)"
                context_info = ""
            
            # Récupérer le solde disponible de l'employé
            balance_info = ""
            if leave_request.leave_type.deducts_balance:
                try:
                    remaining = leave_balance_service.get_remaining_balance(leave_request.employee)
                    balance_info = f"""
💼 SOLDE DE CONGÉS DE L'EMPLOYÉ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Solde disponible : {remaining} jour(s)
"""
                except Exception:
                    pass
            
            # URL de validation
            approval_url = f"{settings.SITE_URL}/leave/approvals/{leave_request.pk}/"
            
            # Motif (peut être vide pour les congés payés)
            reason_display = leave_request.reason if leave_request.reason else "Aucun motif spécifié (congés payés)"
            
            message = f"""
Bonjour {validator.get_full_name()},

═══════════════════════════════════════════════════════════
⏳ {validation_type}
═══════════════════════════════════════════════════════════

Une nouvelle demande de congé nécessite votre validation.

👤 EMPLOYÉ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nom : {leave_request.employee.get_full_name()}
{"Département : " + leave_request.employee.employee_profile.department.name if hasattr(leave_request.employee, 'employee_profile') and leave_request.employee.employee_profile.department else ""}

📋 DÉTAILS DE LA DEMANDE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type de congé : {leave_request.leave_type.name}
Période : Du {leave_request.start_date.strftime('%d/%m/%Y')} au {leave_request.end_date.strftime('%d/%m/%Y')}
Durée : {leave_request.duration_days} jour(s)
Motif : {reason_display}
{balance_info}{context_info}
🔗 ACTION REQUISE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Veuillez traiter cette demande en suivant le lien ci-dessous :
{approval_url}

⚠️ IMPORTANT : En cas de rejet, un commentaire expliquant le motif est obligatoire.

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
            
            logger.info(f"Notification envoyée au validateur {validator.email}", extra={
                'leave_request_id': leave_request.id,
                'validator_id': validator.id,
                'validator_role': validator_role,
                'employee_id': leave_request.employee.id
            })
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la notification au validateur: {str(e)}", exc_info=True, extra={
                'leave_request_id': leave_request.id if leave_request else None,
                'validator_id': validator.id if validator else None
            })
            return False



