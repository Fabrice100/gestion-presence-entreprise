"""
Modèles pour la gestion des comptes utilisateurs et des départements.

Ce module contient les modèles Django pour :
- EmployeeProfile : Profil étendu des employés (extension du User Django)
- Department : Départements/équipes de l'entreprise

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone


class Department(models.Model):
    """
    Modèle représentant un département ou équipe de l'entreprise.
    
    Un département regroupe plusieurs employés et peut avoir un manager.
    Utilisé pour l'organisation hiérarchique et les rapports.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom du département",
        help_text="Nom du département (ex: IT, RH, Ventes)"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Description du département et de ses responsabilités"
    )
    
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name="Manager",
        help_text="Manager responsable de ce département"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Département actif ou fermé"
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
        verbose_name = "Département"
        verbose_name_plural = "Départements"
        ordering = ['name']
    
    def __str__(self):
        """Représentation string du département."""
        return self.name
    
    def get_employee_count(self):
        """Retourne le nombre d'employés dans ce département."""
        return self.employees.filter(is_active=True).count()


class EmployeeProfile(models.Model):
    """
    Modèle étendant le User Django avec des informations spécifiques aux employés.
    
    Ce modèle stocke les informations complémentaires nécessaires pour
    le système de gestion de présence et congés.
    """
    
    # Choix pour les rôles
    ROLE_CHOICES = [
        ('employee', 'Employé'),
        ('manager', 'Manager'),
        ('rh_dg', 'RH/DG'),
        ('admin', 'Administrateur'),
    ]
    
    # Choix pour les types d'employés
    EMPLOYEE_TYPE_CHOICES = [
        ('monthly', 'Mensuel'),
        ('daily', 'Journalier'),
        ('intern', 'Stagiaire'),
    ]
    
    # Choix pour les statuts
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('suspended', 'Suspendu'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name="Utilisateur",
        help_text="Compte utilisateur Django associé"
    )
    
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[A-Z0-9]+$',
            message='L\'ID employé doit contenir uniquement des lettres majuscules et des chiffres'
        )],
        verbose_name="ID Employé",
        help_text="Identifiant unique de l'employé (ex: EMP001)"
    )
    
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name="Département",
        help_text="Département auquel appartient l'employé"
    )
    
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_employees',
        verbose_name="Manager",
        help_text="Manager direct de cet employé"
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='employee',
        verbose_name="Rôle",
        help_text="Rôle de l'employé dans le système"
    )
    
    employee_type = models.CharField(
        max_length=20,
        choices=EMPLOYEE_TYPE_CHOICES,
        default='monthly',
        verbose_name="Type d'employé",
        help_text="Type de contrat de l'employé"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Statut",
        help_text="Statut de l'employé"
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?[0-9\s\-\(\)]+$',
            message='Numéro de téléphone invalide'
        )],
        verbose_name="Téléphone",
        help_text="Numéro de téléphone de l'employé"
    )
    
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name="Adresse",
        help_text="Adresse de l'employé"
    )
    
    hire_date = models.DateField(
        default=timezone.now,
        verbose_name="Date d'embauche",
        help_text="Date d'embauche de l'employé"
    )
    
    contract_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fin de contrat",
        help_text="Date de fin de contrat (si applicable)"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Employé actif dans le système"
    )
    
    can_punch = models.BooleanField(
        default=True,
        verbose_name="Peut pointer",
        help_text="L'employé peut-il pointer (false pour DG/Admin)"
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
        verbose_name = "Profil Employé"
        verbose_name_plural = "Profils Employés"
        ordering = ['employee_id']
    
    def __str__(self):
        """Représentation string du profil employé."""
        return f"{self.employee_id} - {self.user.get_full_name() or self.user.username}"
    
    def get_full_name(self):
        """Retourne le nom complet de l'employé."""
        return self.user.get_full_name() or self.user.username
    
    def is_manager(self):
        """Vérifie si l'employé est un manager."""
        return self.role == 'manager'
    
    def is_rh_dg(self):
        """Vérifie si l'employé est RH/DG."""
        return self.role == 'rh_dg'
    
    def is_admin(self):
        """Vérifie si l'employé est administrateur."""
        return self.role == 'admin'
    
    def can_validate_leave_requests(self):
        """Vérifie si l'employé peut valider des demandes de congés."""
        return self.role in ['manager', 'rh_dg']
    
    def get_managed_employees(self):
        """Retourne la liste des employés gérés par ce manager."""
        if self.role == 'manager':
            return User.objects.filter(managed_employees=self.user)
        return User.objects.none()
    
    def get_department_employees(self):
        """Retourne la liste des employés du même département."""
        if self.department:
            return User.objects.filter(
                employee_profile__department=self.department,
                employee_profile__is_active=True
            )
        return User.objects.none()


# Signal pour créer automatiquement un profil employé lors de la création d'un utilisateur
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    """
    Signal créant automatiquement un EmployeeProfile lors de la création d'un User.
    
    Ce signal s'assure que chaque utilisateur a un profil employé associé.
    """
    if created:
        # Générer un ID employé unique
        last_profile = EmployeeProfile.objects.order_by('-id').first()
        if last_profile:
            last_id = int(last_profile.employee_id[3:]) if last_profile.employee_id.startswith('EMP') else 0
            new_id = f"EMP{last_id + 1:03d}"
        else:
            new_id = "EMP001"
        
        EmployeeProfile.objects.create(
            user=instance,
            employee_id=new_id
        )

@receiver(post_save, sender=User)
def save_employee_profile(sender, instance, **kwargs):
    """
    Signal sauvegardant automatiquement le profil employé lors de la sauvegarde d'un User.
    """
    if hasattr(instance, 'employee_profile'):
        instance.employee_profile.save()
