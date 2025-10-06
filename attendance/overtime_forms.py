"""
Formulaires pour la gestion des heures supplémentaires.

Ce module contient les formulaires Django pour :
- OvertimeRequestForm : Création/modification d'une demande d'heures supplémentaires
- OvertimeApprovalForm : Validation d'une demande

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, datetime, timedelta

from .models import OvertimeRequest, OvertimeConfiguration


class OvertimeRequestForm(forms.ModelForm):
    """
    Formulaire pour la création d'une demande d'heures supplémentaires.
    """

    class Meta:
        model = OvertimeRequest
        fields = ['overtime_type', 'date', 'start_time', 'end_time', 'reason']
        widgets = {
            'overtime_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat()
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez le motif de votre demande d\'heures supplémentaires...'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Initialiser la date par défaut (demain)
        if not self.instance.pk:
            self.fields['date'].initial = (timezone.now().date() + timedelta(days=1))

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date = cleaned_data.get('date')

        if start_time and end_time and date:
            # Vérifier que l'heure de fin est après l'heure de début
            start_datetime = datetime.combine(date, start_time)
            end_datetime = datetime.combine(date, end_time)
            
            # Gérer le cas où end_time est le lendemain
            if end_datetime <= start_datetime:
                end_datetime += timedelta(days=1)
            
            # Calculer la durée
            duration = end_datetime - start_datetime
            hours = duration.total_seconds() / 3600
            
            # Vérifier que la durée est raisonnable (max 12h par jour)
            if hours > 12:
                raise ValidationError('La durée maximale d\'heures supplémentaires est de 12 heures par jour.')
            
            if hours < 0.5:
                raise ValidationError('La durée minimale d\'heures supplémentaires est de 30 minutes.')
            
            # Vérifier que ce n'est pas dans le passé
            if date < timezone.now().date():
                raise ValidationError('Vous ne pouvez pas demander des heures supplémentaires pour une date passée.')
            
            # Vérifier que ce n'est pas trop loin dans le futur (max 30 jours)
            max_future_date = timezone.now().date() + timedelta(days=30)
            if date > max_future_date:
                raise ValidationError('Vous ne pouvez pas demander des heures supplémentaires plus de 30 jours à l\'avance.')

        return cleaned_data

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date:
            # Vérifier que ce n'est pas un weekend (pour les demandes planifiées)
            if date.weekday() >= 5:  # Samedi = 5, Dimanche = 6
                overtime_type = self.cleaned_data.get('overtime_type')
                if overtime_type == 'planned':
                    raise ValidationError('Les heures supplémentaires planifiées ne peuvent pas être demandées pour un weekend.')
        return date

    def clean_start_time(self):
        start_time = self.cleaned_data.get('start_time')
        if start_time:
            # Vérifier que l'heure de début est dans une plage raisonnable
            hour = start_time.hour
            if hour < 6 or hour > 23:
                raise ValidationError('L\'heure de début doit être entre 06:00 et 23:00.')
        return start_time

    def clean_end_time(self):
        end_time = self.cleaned_data.get('end_time')
        if end_time:
            # Vérifier que l'heure de fin est dans une plage raisonnable
            hour = end_time.hour
            if hour < 7 or hour > 23:
                raise ValidationError('L\'heure de fin doit être entre 07:00 et 23:00.')
        return end_time

    def clean_reason(self):
        reason = self.cleaned_data.get('reason')
        if reason:
            # Vérifier que le motif n'est pas trop court
            if len(reason.strip()) < 10:
                raise ValidationError('Le motif doit contenir au moins 10 caractères.')
        return reason


class OvertimeApprovalForm(forms.Form):
    """
    Formulaire pour la validation d'une demande d'heures supplémentaires.
    """
    
    DECISION_CHOICES = [
        ('approved', 'Approuver'),
        ('rejected', 'Rejeter'),
    ]
    
    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        label="Décision",
        help_text="Choisissez votre décision concernant cette demande"
    )
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ajoutez un commentaire (optionnel)...'
        }),
        label="Commentaire",
        help_text="Commentaire ou motif de votre décision",
        required=False
    )

    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        decision = self.cleaned_data.get('decision')
        
        # Si la décision est rejetée, un commentaire est fortement recommandé
        if decision == 'rejected' and not comment:
            raise ValidationError(
                'Un commentaire est fortement recommandé lors du rejet d\'une demande.'
            )
        
        return comment


class OvertimeConfigurationForm(forms.ModelForm):
    """
    Formulaire pour la configuration des règles d'heures supplémentaires.
    """

    class Meta:
        model = OvertimeConfiguration
        fields = [
            'name', 'config_type', 'daily_hours_limit', 'weekly_hours_limit',
            'night_start_hour', 'night_end_hour', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la configuration'
            }),
            'config_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'daily_hours_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '24',
                'step': '0.25'
            }),
            'weekly_hours_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '168',
                'step': '0.25'
            }),
            'night_start_hour': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'night_end_hour': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        config_type = cleaned_data.get('config_type')
        night_start_hour = cleaned_data.get('night_start_hour')
        night_end_hour = cleaned_data.get('night_end_hour')
        daily_hours_limit = cleaned_data.get('daily_hours_limit')
        weekly_hours_limit = cleaned_data.get('weekly_hours_limit')

        # Vérifier les heures de nuit pour le type 'night'
        if config_type == 'night':
            if not night_start_hour or not night_end_hour:
                raise ValidationError('Les heures de début et fin de nuit sont obligatoires pour ce type de configuration.')
        
        # Vérifier que daily_hours_limit est inférieur à weekly_hours_limit
        if daily_hours_limit and weekly_hours_limit:
            if daily_hours_limit > weekly_hours_limit:
                raise ValidationError('La limite d\'heures quotidiennes ne peut pas être supérieure à la limite hebdomadaire.')

        return cleaned_data

    def clean_daily_hours_limit(self):
        daily_hours_limit = self.cleaned_data.get('daily_hours_limit')
        if daily_hours_limit is not None and (daily_hours_limit < 0 or daily_hours_limit > 24):
            raise ValidationError('La limite d\'heures quotidiennes doit être entre 0 et 24 heures.')
        return daily_hours_limit

    def clean_weekly_hours_limit(self):
        weekly_hours_limit = self.cleaned_data.get('weekly_hours_limit')
        if weekly_hours_limit is not None and (weekly_hours_limit < 0 or weekly_hours_limit > 168):
            raise ValidationError('La limite d\'heures hebdomadaires doit être entre 0 et 168 heures.')
        return weekly_hours_limit

