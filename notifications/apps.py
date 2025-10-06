"""
Configuration de l'application notifications.

Ce module configure l'application pour la gestion des notifications :
- Emails automatiques
- Notifications en temps réel
- Rappels et alertes

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = 'Notifications'
    
    def ready(self):
        """
        Importe les signaux quand l'application est prête.
        """
        import notifications.signals