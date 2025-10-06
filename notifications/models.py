"""
Modèles pour le système de notifications.

Ce module contient les modèles pour :
- Notification : Notifications système
- EmailTemplate : Templates d'emails
- NotificationSettings : Paramètres de notifications

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class EmailTemplate(models.Model):
    """
    Modèle pour les templates d'emails.
    """
    
    TEMPLATE_TYPES = [
        ('leave_request_created', 'Demande de congé créée'),
        ('leave_request_approved_manager', 'Congé approuvé par manager'),
        ('leave_request_rejected_manager', 'Congé rejeté par manager'),
        ('leave_request_approved_rh', 'Congé approuvé par RH/DG'),
        ('leave_request_rejected_rh', 'Congé rejeté par RH/DG'),
        ('leave_reminder', 'Rappel de congé'),
        ('attendance_anomaly', 'Anomalie de présence'),
        ('password_reset', 'Réinitialisation de mot de passe'),
        ('welcome', 'Message de bienvenue'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name="Nom du template",
        help_text="Nom descriptif du template"
    )
    
    template_type = models.CharField(
        max_length=50,
        choices=TEMPLATE_TYPES,
        unique=True,
        verbose_name="Type de template",
        help_text="Type de notification"
    )
    
    subject = models.CharField(
        max_length=200,
        verbose_name="Sujet",
        help_text="Sujet de l'email"
    )
    
    html_content = models.TextField(
        verbose_name="Contenu HTML",
        help_text="Contenu HTML de l'email"
    )
    
    text_content = models.TextField(
        blank=True,
        verbose_name="Contenu texte",
        help_text="Contenu texte alternatif"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Template disponible"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Template d'email"
        verbose_name_plural = "Templates d'emails"
        ordering = ['template_type']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"
    
    def render(self, context=None):
        """
        Rend le template avec le contexte fourni.
        """
        if context is None:
            context = {}
        
        # Rendu du contenu HTML
        html_content = render_to_string(
            'notifications/email_template.html',
            {**context, 'email_content': self.html_content}
        )
        
        # Rendu du contenu texte
        text_content = self.text_content or strip_tags(self.html_content)
        
        return {
            'subject': self.subject.format(**context),
            'html_content': html_content,
            'text_content': text_content
        }


class Notification(models.Model):
    """
    Modèle pour les notifications système.
    """
    
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('success', 'Succès'),
        ('warning', 'Avertissement'),
        ('error', 'Erreur'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Faible'),
        ('normal', 'Normal'),
        ('high', 'Élevé'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Utilisateur",
        help_text="Utilisateur destinataire"
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name="Titre",
        help_text="Titre de la notification"
    )
    
    message = models.TextField(
        verbose_name="Message",
        help_text="Contenu de la notification"
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='info',
        verbose_name="Type",
        help_text="Type de notification"
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_LEVELS,
        default='normal',
        verbose_name="Priorité",
        help_text="Niveau de priorité"
    )
    
    is_read = models.BooleanField(
        default=False,
        verbose_name="Lu",
        help_text="Notification lue"
    )
    
    is_sent = models.BooleanField(
        default=False,
        verbose_name="Envoyé",
        help_text="Email envoyé"
    )
    
    action_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL d'action",
        help_text="Lien vers l'action à effectuer"
    )
    
    action_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Texte d'action",
        help_text="Texte du bouton d'action"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    read_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de lecture"
    )
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """
        Marque la notification comme lue.
        """
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def send_email(self):
        """
        Envoie la notification par email.
        """
        if not self.is_sent and self.user.email:
            try:
                send_mail(
                    subject=self.title,
                    message=self.message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[self.user.email],
                    fail_silently=False,
                )
                self.is_sent = True
                self.save()
                return True
            except Exception as e:
                print(f"Erreur envoi email: {e}")
                return False
        return False


class NotificationSettings(models.Model):
    """
    Modèle pour les paramètres de notifications par utilisateur.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_settings',
        verbose_name="Utilisateur"
    )
    
    # Paramètres email
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifications par email",
        help_text="Recevoir les notifications par email"
    )
    
    email_frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immédiat'),
            ('daily', 'Quotidien'),
            ('weekly', 'Hebdomadaire'),
        ],
        default='immediate',
        verbose_name="Fréquence des emails",
        help_text="Fréquence d'envoi des emails"
    )
    
    # Types de notifications
    leave_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifications de congés",
        help_text="Notifications liées aux congés"
    )
    
    attendance_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifications de présence",
        help_text="Notifications liées à la présence"
    )
    
    system_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifications système",
        help_text="Notifications système importantes"
    )
    
    # Horaires
    quiet_hours_start = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Début heures silencieuses",
        help_text="Heure de début des heures silencieuses"
    )
    
    quiet_hours_end = models.TimeField(
        blank=True,
        null=True,
        verbose_name="Fin heures silencieuses",
        help_text="Heure de fin des heures silencieuses"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Paramètres de notifications"
        verbose_name_plural = "Paramètres de notifications"
    
    def __str__(self):
        return f"Paramètres notifications - {self.user.username}"
    
    def should_send_email(self, notification_type=None):
        """
        Détermine si un email doit être envoyé selon les paramètres.
        """
        if not self.email_notifications:
            return False
        
        # Vérifier les types de notifications
        if notification_type == 'leave' and not self.leave_notifications:
            return False
        elif notification_type == 'attendance' and not self.attendance_notifications:
            return False
        elif notification_type == 'system' and not self.system_notifications:
            return False
        
        # Vérifier les heures silencieuses
        if self.quiet_hours_start and self.quiet_hours_end:
            from datetime import datetime, time
            now = datetime.now().time()
            
            if self.quiet_hours_start <= self.quiet_hours_end:
                # Heures silencieuses dans la même journée
                if self.quiet_hours_start <= now <= self.quiet_hours_end:
                    return False
            else:
                # Heures silencieuses sur deux jours
                if now >= self.quiet_hours_start or now <= self.quiet_hours_end:
                    return False
        
        return True
