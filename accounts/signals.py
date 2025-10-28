"""
Signals pour la gestion automatique des comptes utilisateurs.

Ce module gère :
- Envoi automatique d'email avec ID et MDP temporaire à la création de compte
- Génération de mot de passe temporaire sécurisé
- Activation du flag must_change_password pour forcer changement à la 1ère connexion

Conforme aux spécifications: MODULE 3 - Création de Compte Sécurisée
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def send_account_creation_email(sender, instance, created, **kwargs):
    """
    Signal post_save : Envoie automatiquement un email avec identifiants
    lorsqu'un nouveau compte utilisateur est créé par le RH.
    
    Fonctionnalité:
    1. Génère un mot de passe temporaire sécurisé (12 caractères)
    2. Définit ce mot de passe pour l'utilisateur
    3. Active le flag must_change_password dans EmployeeProfile
    4. Envoie un email avec l'ID et le MDP temporaire
    
    Args:
        sender: Model User
        instance: Instance User créée
        created: Boolean indiquant si c'est une création (True) ou mise à jour (False)
        **kwargs: Arguments supplémentaires
    """
    # Traiter seulement les nouvelles créations
    if not created:
        return
    
    # Ignorer les superusers (créés via createsuperuser)
    if instance.is_superuser:
        logger.info(f"Superuser créé: {instance.username} - pas d'email envoyé")
        return
    
    # Vérifier que l'email existe
    if not instance.email:
        logger.warning(f"Utilisateur {instance.username} créé sans email - impossible d'envoyer les identifiants")
        return
    
    try:
        # 1. Générer un mot de passe temporaire sécurisé
        temporary_password = get_random_string(
            length=12,
            allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
        )
        
        # 2. Définir le mot de passe temporaire
        instance.set_password(temporary_password)
        instance.save(update_fields=['password'])
        
        # 3. Activer le flag force_password_change dans EmployeeProfile
        # (sera créé automatiquement par post_save si n'existe pas)
        from accounts.models import EmployeeProfile
        profile, profile_created = EmployeeProfile.objects.get_or_create(user=instance)
        profile.force_password_change = True
        profile.save(update_fields=['force_password_change'])
        
        # 4. Préparer le contenu de l'email
        subject = f"Bienvenue - Vos identifiants pour {settings.SITE_NAME}"
        
        message = f"""
Bonjour {instance.get_full_name() or instance.username},

Votre compte a été créé avec succès dans le système de gestion de présence.

Voici vos identifiants de connexion :

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Identifiant (ID) : {instance.username}
  Mot de passe temporaire : {temporary_password}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ IMPORTANT : Pour des raisons de sécurité, vous DEVEZ changer ce mot de passe
lors de votre première connexion.

🔗 URL de connexion : {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}/accounts/login/

Instructions :
1. Rendez-vous sur l'URL ci-dessus
2. Connectez-vous avec vos identifiants
3. Vous serez automatiquement redirigé pour changer votre mot de passe
4. Choisissez un mot de passe fort (minimum 8 caractères)

Besoin d'aide ? Contactez le service RH.

Cordialement,
L'équipe RH
        """
        
        # 5. Envoyer l'email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            fail_silently=False,  # Lever une exception en cas d'erreur
        )
        
        logger.info(f"Email envoyé avec succès à {instance.email} pour l'utilisateur {instance.username}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email pour {instance.username}: {str(e)}")
        # Ne pas empêcher la création du compte si l'email échoue
        pass
