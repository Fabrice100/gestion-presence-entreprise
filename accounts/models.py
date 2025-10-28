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


class WorkSchedule(models.Model):
    """
    Profil horaire réutilisable définissant les horaires contractuels.
    
    Exemples de profils :
    - Bureau Standard : 8h-18h avec pause 12h-14h
    - Mi-temps : 8h-12h sans pause
    - Équipe Nuit : 20h-4h avec pause 23h-23h30
    
    Permet de :
    - Corriger les heures de pointage selon le contrat
    - Gérer plusieurs équipes avec horaires différents
    - Maintenir l'historique des affectations
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom du profil",
        help_text="Ex: Bureau Standard, Mi-temps, Équipe Matin"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Description du profil horaire et à qui il s'applique"
    )
    
    # Horaires contractuels
    start_time = models.TimeField(
        verbose_name="Heure début contrat (HDC)",
        help_text="Heure de début contractuelle (ex: 8h00)"
    )
    
    end_time = models.TimeField(
        verbose_name="Heure fin contrat (HFC)",
        help_text="Heure de fin contractuelle (ex: 18h00)"
    )
    
    # Pause
    pause_start = models.TimeField(
        verbose_name="Début de pause",
        help_text="Heure de début de la pause (ex: 12h00)"
    )
    
    pause_end = models.TimeField(
        verbose_name="Fin de pause",
        help_text="Heure de fin de la pause (ex: 14h00)"
    )
    
    # Profil par défaut
    is_default = models.BooleanField(
        default=False,
        verbose_name="Profil par défaut",
        help_text="Utilisé pour les nouveaux employés si aucun profil spécifié"
    )
    
    # Traçabilité
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_schedules',
        verbose_name="Créé par",
        help_text="Utilisateur (RH) qui a créé ce profil"
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
        verbose_name = "Profil Horaire"
        verbose_name_plural = "Profils Horaires"
        ordering = ['name']
    
    def __str__(self):
        """Représentation string du profil horaire."""
        return f"{self.name} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"
    
    def get_pause_duration_hours(self):
        """Calcule la durée de la pause en heures décimales."""
        from datetime import datetime, date
        from decimal import Decimal
        
        today = date.today()
        start_dt = datetime.combine(today, self.pause_start)
        end_dt = datetime.combine(today, self.pause_end)
        
        duration_seconds = (end_dt - start_dt).total_seconds()
        return Decimal(str(duration_seconds / 3600)).quantize(Decimal('0.01'))
    
    def get_contractual_duration_hours(self):
        """Calcule la durée contractuelle totale (sans pause) en heures."""
        from datetime import datetime, date
        from decimal import Decimal
        
        today = date.today()
        start_dt = datetime.combine(today, self.start_time)
        end_dt = datetime.combine(today, self.end_time)
        
        # Si fin < début, c'est le lendemain (équipe de nuit)
        if end_dt < start_dt:
            from datetime import timedelta
            end_dt += timedelta(days=1)
        
        total_seconds = (end_dt - start_dt).total_seconds()
        total_hours = Decimal(str(total_seconds / 3600))
        
        # Soustraire la pause
        pause_hours = self.get_pause_duration_hours()
        return (total_hours - pause_hours).quantize(Decimal('0.01'))
    
    def get_employee_count(self):
        """Retourne le nombre d'employés actuellement sur ce profil."""
        return self.employees.filter(is_active=True).count()


class EmployeeScheduleHistory(models.Model):
    """
    Historique des affectations de profils horaires aux employés.
    
    IMMUABILITÉ : Cette table garantit que les données passées ne sont jamais modifiées.
    Chaque changement de profil crée une nouvelle ligne avec dates de début/fin.
    
    Permet de :
    - Recalculer les paies des mois précédents avec les bons profils
    - Audit trail complet des changements d'horaires
    - Conformité légale (preuve du contrat à une date donnée)
    
    Exemple :
    - Jean | Bureau | 01/01/2025 | 14/03/2025 | RH_Marie
    - Jean | Mi-temps | 15/03/2025 | NULL | RH_Marie
    """
    
    employee = models.ForeignKey(
        'EmployeeProfile',
        on_delete=models.CASCADE,
        related_name='schedule_history',
        verbose_name="Employé"
    )
    
    work_schedule = models.ForeignKey(
        WorkSchedule,
        on_delete=models.PROTECT,  # Empêche suppression si historique existe
        related_name='history_entries',
        verbose_name="Profil horaire"
    )
    
    assigned_date = models.DateField(
        verbose_name="Date d'affectation",
        help_text="Date à partir de laquelle ce profil est actif pour l'employé"
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin",
        help_text="NULL si c'est le profil actif, sinon date de fin d'utilisation"
    )
    
    # Traçabilité
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='schedule_assignments',
        verbose_name="Assigné par",
        help_text="Utilisateur (RH) qui a fait l'affectation"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'enregistrement"
    )
    
    class Meta:
        verbose_name = "Historique Profil Horaire"
        verbose_name_plural = "Historiques Profils Horaires"
        ordering = ['-assigned_date']
        indexes = [
            models.Index(fields=['employee', 'assigned_date', 'end_date']),
        ]
    
    def __str__(self):
        """Représentation string de l'historique."""
        status = "actif" if self.end_date is None else f"jusqu'au {self.end_date}"
        return f"{self.employee} - {self.work_schedule.name} ({status})"
    
    def is_active(self):
        """Vérifie si cet historique est actuellement actif."""
        return self.end_date is None


class EmployeeProfile(models.Model):
    """
    Modèle étendant le User Django avec des informations spécifiques aux employés.
    
    Ce modèle stocke les informations complémentaires nécessaires pour
    le système de gestion de présence et congés.
    """
    
    # Choix pour les rôles (3 rôles métier seulement)
    # Note: Admin technique = Django superuser (pas de EmployeeProfile)
    ROLE_CHOICES = [
        ('employee', 'Employé'),
        ('manager', 'Manager'),
        ('rh', 'RH'),
    ]
    
    # Choix pour les types d'employés
    EMPLOYEE_TYPE_CHOICES = [
        ('monthly', 'Mensuel'),
        ('daily', 'Journalier'),
        ('intern', 'Stagiaire'),
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
    
    force_password_change = models.BooleanField(
        default=False,
        verbose_name="Changement de mot de passe requis",
        help_text="L'employé doit changer son mot de passe à la prochaine connexion"
    )
    
    # Profil horaire actuel
    current_work_schedule = models.ForeignKey(
        WorkSchedule,
        on_delete=models.PROTECT,
        null=True,  # Temporaire pour migration - sera NOT NULL après
        blank=True,
        related_name='employees',
        verbose_name="Profil horaire actuel",
        help_text="Profil horaire actuellement appliqué à cet employé"
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
    
    def is_rh(self):
        """Vérifie si l'employé est RH."""
        return self.role == 'rh'
    
    # Note: is_admin() supprimée - Utiliser user.is_superuser pour admin technique
    
    def can_validate_leave_requests(self):
        """Vérifie si l'employé peut valider des demandes de congés."""
        return self.role in ['manager', 'rh']
    
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


# Signals pour automatisation
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=EmployeeProfile)
def assign_department_manager(sender, instance, **kwargs):
    """
    Assigne automatiquement le manager du département à l'employé
    si aucun manager n'est spécifié.
    """
    # Si l'employé a un département mais pas de manager
    if instance.department and not instance.manager:
        # Si le département a un manager
        if instance.department.manager:
            # Assigner le manager du département
            instance.manager = instance.department.manager

@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    """
    Signal créant automatiquement un EmployeeProfile lors de la création d'un User.
    
    Ce signal s'assure que chaque utilisateur a un profil employé associé.
    Génère un ID aléatoire non successif pour renforcer la sécurité.
    """
    if created:
        # Générer un ID employé unique aléatoire
        import random
        prefix = 'EMP'
        
        # Récupérer tous les IDs existants
        existing_ids = set(
            EmployeeProfile.objects.filter(
                employee_id__startswith=prefix
            ).values_list('employee_id', flat=True)
        )
        
        # Générer un ID aléatoire unique
        max_attempts = 100
        new_id = None
        
        for _ in range(max_attempts):
            # Générer un nombre aléatoire entre 100 et 999
            random_number = random.randint(100, 999)
            candidate_id = f'{prefix}{random_number}'
            
            if candidate_id not in existing_ids:
                new_id = candidate_id
                break
        
        # Si pas trouvé dans 100-999, essayer 001-099
        if not new_id:
            for _ in range(max_attempts):
                random_number = random.randint(1, 99)
                candidate_id = f'{prefix}{random_number:03d}'
                
                if candidate_id not in existing_ids:
                    new_id = candidate_id
                    break
        
        # Utiliser l'ID trouvé ou un ID par défaut
        if not new_id:
            new_id = f'{prefix}{random.randint(1000, 9999)}'  # Fallback
        
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