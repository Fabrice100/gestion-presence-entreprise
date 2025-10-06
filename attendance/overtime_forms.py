"""
Formulaires pour la gestion des heures supplémentaires.

Ce module contient les formulaires Django pour :
- OvertimeRecordForm : Modification d'un enregistrement d'heures supplémentaires
- OvertimeApprovalForm : Validation d'un enregistrement
- OvertimeConfigurationForm : Configuration des règles

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .overtime_models import OvertimeRecord, OvertimeConfiguration
from accounts.models import EmployeeProfile
from datetime import date, timedelta
from decimal import Decimal


class OvertimeRecordForm(forms.ModelForm):
    """
    Formulaire pour la modification d'un enregistrement d'heures supplémentaires.
    """
    
    class Meta:
        model = OvertimeRecord
        fields = ['manager_decision', 'manager_comment', 'rh_decision', 'rh_comment']
        widgets = {
            'manager_decision': forms.Select(attrs={
                'class': 'form-control'
            }),
            'manager_comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Votre commentaire...'
            }),
            'rh_decision': forms.Select(attrs={
                'class': 'form-control'
            }),
            'rh_comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Votre commentaire...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Désactiver les champs si l'utilisateur n'a pas la permission
        if self.user and self.instance:
            is_manager = self.user.employee_profile.is_manager()
            is_rh_dg = self.user.employee_profile.is_rh_dg()
            
            if is_manager and self.instance.manager != self.user:
                # Un manager ne peut pas valider les enregistrements d'un autre manager
                for field in ['manager_decision', 'manager_comment']:
                    self.fields[field].widget.attrs['readonly'] = True
                    self.fields[field].required = False
            
            if is_rh_dg and not is_manager:  # RH/DG ne doit pas toucher aux champs manager
                for field in ['manager_decision', 'manager_comment']:
                    self.fields[field].widget.attrs['readonly'] = True
                    self.fields[field].required = False
            
            if is_manager and not is_rh_dg:  # Manager ne doit pas toucher aux champs RH
                for field in ['rh_decision', 'rh_comment']:
                    self.fields[field].widget.attrs['readonly'] = True
                    self.fields[field].required = False
            
            # Si la décision a déjà été prise, rendre les champs readonly
            if self.instance.manager_decision and is_manager:
                self.fields['manager_decision'].widget.attrs['readonly'] = True
                self.fields['manager_comment'].widget.attrs['readonly'] = True
            
            if self.instance.rh_decision and is_rh_dg:
                self.fields['rh_decision'].widget.attrs['readonly'] = True
                self.fields['rh_comment'].widget.attrs['readonly'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.user:
            is_manager = self.user.employee_profile.is_manager()
            is_rh_dg = self.user.employee_profile.is_rh_dg()
            
            if is_manager and self.instance.manager == self.user:
                # Manager valide sa partie
                if not cleaned_data.get('manager_decision'):
                    raise ValidationError("La décision du manager est requise.")
                if cleaned_data.get('manager_decision') == 'rejected' and not cleaned_data.get('manager_comment'):
                    raise ValidationError("Un commentaire est requis pour un rejet par le manager.")
            
            if is_rh_dg:
                # RH/DG valide sa partie
                if not cleaned_data.get('rh_decision'):
                    raise ValidationError("La décision du RH/DG est requise.")
                if cleaned_data.get('rh_decision') == 'rejected' and not cleaned_data.get('rh_comment'):
                    raise ValidationError("Un commentaire est requis pour un rejet par le RH/DG.")
        
        return cleaned_data


class OvertimeApprovalForm(forms.Form):
    """
    Formulaire simple pour l'approbation/rejet d'un enregistrement.
    """
    
    DECISION_CHOICES = [
        ('approved', 'Approuver'),
        ('rejected', 'Rejeter'),
        ('disputed', 'Contester'),
    ]
    
    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Votre commentaire...'
        }),
        required=False,
        help_text="Commentaire obligatoire pour un rejet ou une contestation"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get('decision')
        comment = cleaned_data.get('comment')
        
        # Si la décision est rejetée, un commentaire est fortement recommandé
        if decision in ['rejected', 'disputed'] and not comment:
            raise ValidationError(
                'Un commentaire est fortement recommandé lors du rejet ou de la contestation d\'un enregistrement.'
            )
        
        return cleaned_data


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