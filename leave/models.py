"""
Modèles pour la gestion des congés et absences.

Ce module contient les modèles Django pour :
- LeaveType : Types de congés disponibles
- LeaveRequest : Demandes de congés avec workflow de validation
- LeaveBalance : Soldes de congés par employé

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from common.validators import (
    validate_reason_text,
    validate_safe_string,
    validate_email_address
)


class LeaveType(models.Model):
    """
    Modèle représentant un type de congé (annuel, maladie, etc.).
    
    Définit les règles et caractéristiques de chaque type de congé.
    """
    
    # Choix pour les unités de calcul
    UNIT_CHOICES = [
        ('days', 'Jours'),
        ('hours', 'Heures'),
    ]
    
    # Choix pour les types d'attribution
    ALLOCATION_CHOICES = [
        ('annual', 'Annuelle'),
        ('monthly', 'Mensuelle'),
        ('on_demand', 'Sur demande'),
    ]
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom du type",
        help_text="Nom du type de congé (ex: Congés payés, Maladie)"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Description du type de congé"
    )
    
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Code",
        help_text="Code court pour identifier le type (ex: CP, MAL)"
    )
    
    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default='days',
        verbose_name="Unité",
        help_text="Unité de calcul (jours ou heures)"
    )
    
    allocation_type = models.CharField(
        max_length=20,
        choices=ALLOCATION_CHOICES,
        default='annual',
        verbose_name="Type d'attribution",
        help_text="Comment les congés sont attribués"
    )
    
    allocation_amount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Montant d'attribution",
        help_text="Quantité attribuée (ex: 25 jours par an)"
    )
    
    max_consecutive_days = models.PositiveIntegerField(
        default=30,
        verbose_name="Maximum consécutif",
        help_text="Nombre maximum de jours consécutifs autorisés"
    )
    
    requires_justification = models.BooleanField(
        default=False,
        verbose_name="Justification requise",
        help_text="Une justification est-elle requise ?"
    )
    
    requires_medical_certificate = models.BooleanField(
        default=False,
        verbose_name="Certificat médical",
        help_text="Un certificat médical est-il requis ?"
    )
    
    advance_notice_days = models.PositiveIntegerField(
        default=0,
        verbose_name="Préavis (jours)",
        help_text="Nombre de jours d'avance requis"
    )
    
    is_paid = models.BooleanField(
        default=True,
        verbose_name="Rémunéré",
        help_text="Le congé est-il rémunéré ?"
    )
    
    deducts_balance = models.BooleanField(
        default=True,
        verbose_name="Déduit du solde",
        help_text="Ce type de congé déduit-il du solde annuel ? (Faux pour congés exceptionnels/maladie)"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Type de congé disponible"
    )
    
    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name="Couleur",
        help_text="Couleur hexadécimale pour l'affichage"
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
        verbose_name = "Type de congé"
        verbose_name_plural = "Types de congés"
        ordering = ['name']
    
    def __str__(self):
        """Représentation string du type de congé."""
        return self.name


class LeaveRequest(models.Model):
    """
    Modèle représentant une demande de congé avec workflow de validation.
    
    Gère le processus de demande, validation et approbation des congés.
    """
    
    # Choix pour les statuts
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved_manager', 'Approuvé par Manager'),
        ('approved_rh', 'Approuvé par RH'),
        ('rejected_manager', 'Rejeté par Manager'),
        ('rejected_rh', 'Rejeté par RH'),
        ('cancelled', 'Annulé'),
    ]
    
    # Choix pour les priorités
    PRIORITY_CHOICES = [
        ('low', 'Basse'),
        ('normal', 'Normale'),
        ('high', 'Haute'),
        ('urgent', 'Urgente'),
    ]
    
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leave_requests',
        verbose_name="Employé",
        help_text="Employé qui fait la demande"
    )
    
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='requests',
        verbose_name="Type de congé",
        help_text="Type de congé demandé"
    )
    
    start_date = models.DateField(
        verbose_name="Date de début",
        help_text="Date de début du congé"
    )
    
    end_date = models.DateField(
        verbose_name="Date de fin",
        help_text="Date de fin du congé"
    )
    
    duration_days = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Durée (jours)",
        help_text="Durée du congé en jours"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut",
        help_text="Statut actuel de la demande"
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name="Priorité",
        help_text="Priorité de la demande"
    )
    
    reason = models.TextField(
        validators=[validate_reason_text],
        verbose_name="Motif",
        help_text="Motif de la demande de congé"
    )
    
    justification = models.TextField(
        blank=True,
        null=True,
        validators=[validate_reason_text],
        verbose_name="Justification",
        help_text="Justification détaillée si nécessaire"
    )
    
    medical_certificate = models.FileField(
        upload_to='medical_certificates/',
        blank=True,
        null=True,
        verbose_name="Certificat médical",
        help_text="Certificat médical si requis"
    )
    
    # Workflow de validation
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_leave_requests',
        verbose_name="Manager",
        help_text="Manager responsable de la validation"
    )
    
    manager_decision = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name="Décision Manager",
        help_text="Décision du manager"
    )
    
    manager_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire Manager",
        help_text="Commentaire du manager"
    )
    
    manager_decision_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Décision Manager le",
        help_text="Date de décision du manager"
    )
    
    rh_decision = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name="Décision RH",
        help_text="Décision du RH"
    )
    
    rh_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire RH",
        help_text="Commentaire du RH"
    )
    
    rh_decision_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Décision RH le",
        help_text="Date de décision du RH"
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
        verbose_name = "Demande de congé"
        verbose_name_plural = "Demandes de congés"
        ordering = ['-created_at']
    
    def __str__(self):
        """Représentation string de la demande de congé."""
        return f"{self.employee.get_full_name()} - {self.leave_type.name} ({self.start_date} - {self.end_date})"
    
    def save(self, *args, **kwargs):
        """
        Override de la méthode save pour calculer automatiquement la durée.
        """
        if self.start_date and self.end_date:
            self.duration_days = (self.end_date - self.start_date).days + 1
        
        super().save(*args, **kwargs)
    
    def get_workflow_status(self):
        """
        Retourne le statut actuel du workflow.
        """
        if self.status == 'cancelled':
            return 'Annulé'
        elif self.status == 'approved_rh':
            return 'Approuvé'
        elif self.status == 'rejected_rh':
            return 'Rejeté'
        elif self.rh_decision:
            return f'RH: {self.get_rh_decision_display()}'
        elif self.manager_decision:
            return f'Manager: {self.get_manager_decision_display()}'
        else:
            return 'En attente Manager'
    
    def can_be_approved_by(self, user):
        """
        Vérifie si un utilisateur peut approuver cette demande.
        """
        from accounts.models import EmployeeProfile
        
        try:
            profile = user.employee_profile
        except EmployeeProfile.DoesNotExist:
            return False
        
        # Si c'est le RH, il peut toujours approuver
        if profile.is_rh():
            return True
        
        # Si c'est un manager, il peut approuver les demandes de son équipe
        if profile.is_manager() and self.employee.employee_profile.manager == user:
            return True
        
        return False
    
    def approve_by_manager(self, user, comment=None):
        """
        Approuve la demande par le manager.
        """
        self.manager = user
        self.manager_decision = 'approved_manager'
        self.manager_comment = comment
        self.manager_decision_at = timezone.now()
        self.status = 'approved_manager'
        self.save()
    
    def reject_by_manager(self, user, comment):
        """
        Rejette la demande par le manager.
        """
        self.manager = user
        self.manager_decision = 'rejected_manager'
        self.manager_comment = comment
        self.manager_decision_at = timezone.now()
        self.status = 'rejected_manager'
        self.save()
    
    def approve_by_rh(self, user, comment=None):
        """
        Approuve la demande par le RH.
        """
        self.rh_decision = 'approved_rh'
        self.rh_comment = comment
        self.rh_decision_at = timezone.now()
        self.status = 'approved_rh'
        self.save()
    
    def reject_by_rh(self, user, comment):
        """
        Rejette la demande par le RH.
        """
        self.rh_decision = 'rejected_rh'
        self.rh_comment = comment
        self.rh_decision_at = timezone.now()
        self.status = 'rejected_rh'
        self.save()
    
    def cancel(self):
        """
        Annule la demande.
        """
        self.status = 'cancelled'
        self.save()
    
    def is_overlapping_with(self, other_request):
        """
        Vérifie si cette demande chevauche avec une autre.
        """
        return not (self.end_date < other_request.start_date or 
                   self.start_date > other_request.end_date)
    
    def get_remaining_balance(self):
        """
        Calcule le solde restant du SOLDE UNIQUE de 30 jours.
        
        IMPORTANT : Tous les congés payés partagent le même solde.
        """
        from .models import LeaveBalance, LeaveType
        
        # Récupérer le type "Congés payés" (solde unique)
        conges_payes_type = LeaveType.objects.filter(name__icontains='payé').first()
        
        if not conges_payes_type:
            return 0
        
        # Toujours utiliser le solde "Congés payés"
        balance = LeaveBalance.objects.filter(
            employee=self.employee,
            leave_type=conges_payes_type  # Solde unique
        ).first()
        
        if balance:
            return balance.remaining_balance
        
        return 0


class LeaveBalance(models.Model):
    """
    Modèle représentant le solde de congés d'un employé pour un type donné.
    
    Suit les congés acquis, pris et restants.
    """
    
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='leave_balances',
        verbose_name="Employé",
        help_text="Employé concerné"
    )
    
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='balances',
        verbose_name="Type de congé",
        help_text="Type de congé"
    )
    
    year = models.PositiveIntegerField(
        default=2024,
        verbose_name="Année",
        help_text="Année de référence"
    )
    
    allocated_balance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Solde alloué",
        help_text="Congés alloués pour l'année"
    )
    
    taken_balance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Solde pris",
        help_text="Congés pris pendant l'année"
    )
    
    carried_over_balance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Solde reporté",
        help_text="Congés reportés de l'année précédente"
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
        verbose_name = "Solde de congé"
        verbose_name_plural = "Soldes de congés"
        unique_together = ['employee', 'leave_type', 'year']
        ordering = ['employee', 'leave_type', '-year']
    
    def __str__(self):
        """Représentation string du solde de congé."""
        return f"{self.employee.get_full_name()} - {self.leave_type.name} ({self.year})"
    
    @property
    def remaining_balance(self):
        """
        Calcule le solde restant disponible.
        """
        return self.allocated_balance + self.carried_over_balance - self.taken_balance
    
    @property
    def total_balance(self):
        """
        Calcule le solde total disponible.
        """
        return self.allocated_balance + self.carried_over_balance
    
    def can_take_leave(self, duration):
        """
        Vérifie si l'employé peut prendre des congés de la durée spécifiée.
        """
        return self.remaining_balance >= duration
    
    def take_leave(self, duration):
        """
        Déduit la durée des congés du solde.
        """
        self.taken_balance += duration
        self.save()
    
    def return_leave(self, duration):
        """
        Restaure la durée des congés au solde.
        """
        self.taken_balance -= duration
        self.save()
    
    @classmethod
    def create_annual_balance(cls, employee, year=None):
        """
        Crée les soldes annuels pour un employé.
        """
        if year is None:
            year = timezone.now().year
        
        # Récupérer les types de congés actifs
        leave_types = LeaveType.objects.filter(is_active=True)
        
        for leave_type in leave_types:
            # Calculer le solde alloué selon le type d'attribution
            if leave_type.allocation_type == 'annual':
                allocated = leave_type.allocation_amount
            elif leave_type.allocation_type == 'monthly':
                allocated = leave_type.allocation_amount * 12
            else:
                allocated = 0
            
            # Créer ou mettre à jour le solde
            balance, created = cls.objects.get_or_create(
                employee=employee,
                leave_type=leave_type,
                year=year,
                defaults={'allocated_balance': allocated}
            )
            
            if not created:
                balance.allocated_balance = allocated
                balance.save()


class Holiday(models.Model):
    """
    Modèle représentant les jours fériés et congés légaux.
    
    Utilisé pour exclure ces jours du calcul des congés et pointages.
    """
    
    # Choix pour les types de jours fériés
    TYPE_CHOICES = [
        ('national', 'Férié national'),
        ('regional', 'Férié régional'),
        ('company', 'Jour de l\'entreprise'),
        ('religious', 'Fête religieuse'),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name="Nom",
        help_text="Nom du jour férié"
    )
    
    date = models.DateField(
        verbose_name="Date",
        help_text="Date du jour férié"
    )
    
    holiday_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='national',
        verbose_name="Type",
        help_text="Type de jour férié"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Description",
        help_text="Description du jour férié"
    )
    
    is_recurring = models.BooleanField(
        default=False,
        verbose_name="Récurrent",
        help_text="Ce jour férié se répète chaque année"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Jour férié actif"
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
        verbose_name = "Jour férié"
        verbose_name_plural = "Jours fériés"
        ordering = ['date']
    
    def __str__(self):
        """Représentation string du jour férié."""
        return f"{self.name} ({self.date})"
    
    @classmethod
    def get_holidays_for_year(cls, year):
        """
        Retourne tous les jours fériés pour une année donnée.
        """
        holidays = cls.objects.filter(
            is_active=True,
            date__year=year
        )
        
        # Ajouter les jours fériés récurrents
        recurring_holidays = cls.objects.filter(
            is_active=True,
            is_recurring=True
        )
        
        result = list(holidays)
        for holiday in recurring_holidays:
            # Créer une nouvelle date avec l'année spécifiée
            recurring_date = holiday.date.replace(year=year)
            holiday_copy = cls(
                name=holiday.name,
                date=recurring_date,
                holiday_type=holiday.holiday_type,
                description=holiday.description,
                is_recurring=holiday.is_recurring,
                is_active=holiday.is_active
            )
            result.append(holiday_copy)
        
        return sorted(result, key=lambda x: x.date)
    
    def is_working_day(self):
        """
        Vérifie si c'est un jour ouvrable (lundi-vendredi).
        """
        return self.date.weekday() < 5  # 0-4 = lundi-vendredi