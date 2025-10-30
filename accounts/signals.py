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


# Signal DÉSACTIVÉ pour éviter le double envoi d'email
# L'envoi d'email est géré manuellement depuis hr_views.py avec le template HTML professionnel
# Le signal causait un double envoi (texte brut + HTML template)

# @receiver(post_save, sender=User)
# def send_account_creation_email(sender, instance, created, **kwargs):
#     """
#     Signal post_save DÉSACTIVÉ - L'envoi d'email est géré depuis hr_views.py
#     pour utiliser le template HTML professionnel (welcome_email.html).
#     
#     NOTE: Ce signal était actif mais causait un double envoi d'email :
#     1. Signal envoyait un email texte brut
#     2. hr_views.py envoyait aussi un email HTML via NotificationService
#     
#     Solution: On désactive le signal et on garde seulement l'envoi manuel
#     depuis hr_views.py qui utilise NotificationService.send_welcome_email()
#     avec le template HTML professionnel.
#     """
#     pass
