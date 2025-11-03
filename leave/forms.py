"""
Formulaires pour la gestion des congés.

Ce module contient les formulaires pour :
- Création de demandes de congés
- Validation des demandes
- Gestion des soldes

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from django.utils.html import format_html

from .models import LeaveRequest, LeaveType, LeaveBalance


class LeaveRequestForm(forms.ModelForm):
    """
    Formulaire pour la création d'une demande de congé.
    """
    
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'date',
                'min': date.today().strftime('%Y-%m-%d')
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'date',
                'min': date.today().strftime('%Y-%m-%d')
            }),
            'reason': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Décrivez la raison de votre demande (obligatoire pour "Autre")...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les types de congés disponibles (robuste en cas d'erreur DB)
        try:
            if user:
                # N'afficher que 'Congés payés' (CP) et 'Autre' (CSS)
                available_types = LeaveType.objects.filter(
                    is_active=True,
                    code__in=['CP', 'CSS']
                ).order_by('name')
                self.fields['leave_type'].queryset = available_types
                self.fields['leave_type'].empty_label = "Sélectionner un type de congé"
        except Exception:
            # En cas d'erreur base, éviter l'écran d'erreur et présenter une liste vide
            from django.db.models.query import EmptyQuerySet
            self.fields['leave_type'].queryset = LeaveType.objects.none()
            self.fields['leave_type'].empty_label = "(types indisponibles)"
        
        # Mettre à jour min dynamiquement pour empêcher la sélection de dates passées
        today_str = date.today().strftime('%Y-%m-%d')
        self.fields['start_date'].widget.attrs['min'] = today_str
        self.fields['end_date'].widget.attrs['min'] = today_str
        
        # Rendre le champ reason optionnel par défaut (sera validé dans clean())
        self.fields['reason'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        leave_type = cleaned_data.get('leave_type')
        reason = (cleaned_data.get('reason') or '').strip()
        
        if start_date and end_date:
            # Vérifier que la date de fin est après la date de début
            if end_date < start_date:
                raise ValidationError('La date de fin doit être postérieure à la date de début.')
            
            # Vérifier que les dates ne sont pas dans le passé (sauf congés maladie)
            today = date.today()
            if start_date < today and leave_type and leave_type.name.lower() not in ['maladie', 'sick']:
                raise ValidationError('Les dates de congé ne peuvent pas être dans le passé.')
            
            # Vérifier la durée maximale
            days_requested = (end_date - start_date).days + 1
            if leave_type and leave_type.max_consecutive_days and days_requested > leave_type.max_consecutive_days:
                raise ValidationError(f'La durée maximale pour ce type de congé est de {leave_type.max_consecutive_days} jours.')
        
        # Règle métier: motif facultatif pour Congés payés (CP), obligatoire pour Autre (CSS)
        if leave_type:
            if getattr(leave_type, 'code', '') == 'CSS' and not reason:
                raise ValidationError({'reason': 'Le motif est obligatoire pour le type "Autre".'})
            # Pour les congés payés (CP), le motif peut rester vide (null)
            # Pas besoin de mettre 'N/A', on laisse blank=True faire son travail
        return cleaned_data
    
    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date:
            # Vérifier que ce n'est pas un weekend (pour la plupart des types)
            if start_date.weekday() >= 5:  # Samedi = 5, Dimanche = 6
                raise ValidationError('Les congés ne peuvent généralement pas commencer un weekend.')
        return start_date
    
    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        if end_date:
            # Vérifier que ce n'est pas un weekend (pour la plupart des types)
            if end_date.weekday() >= 5:  # Samedi = 5, Dimanche = 6
                raise ValidationError('Les congés ne peuvent généralement pas se terminer un weekend.')
        return end_date


class LeaveApprovalForm(forms.Form):
    """
    Formulaire pour l'approbation/rejet d'une demande de congé.
    """
    
    ACTION_CHOICES = [
        ('approve', 'Approuver'),
        ('reject', 'Rejeter'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500'
        })
    )
    
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'Commentaire (optionnel)...'
        }),
        help_text="Ajoutez un commentaire pour expliquer votre décision."
    )
    
    def clean(self):
        """
        Validation globale du formulaire.
        Force le commentaire obligatoire lors d'un rejet (BUG CORRIGÉ).
        """
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        comment = cleaned_data.get('comment', '')
        
        # Exiger un commentaire OBLIGATOIRE pour les rejets
        if action == 'reject' and not comment.strip():
            raise ValidationError({
                'comment': 'Un motif de rejet est obligatoire pour assurer la transparence et la traçabilité.'
            })
        
        return cleaned_data
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '')
        return comment


class LeaveBalanceForm(forms.ModelForm):
    """
    Formulaire pour la gestion des soldes de congés (admin/RH).
    """
    
    class Meta:
        model = LeaveBalance
        fields = ['employee', 'leave_type', 'year', 'allocated_balance', 'taken_balance', 'carried_over_balance']
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'leave_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'allocated_balance': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '0.01'
            }),
            'taken_balance': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '0.01'
            }),
            'carried_over_balance': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'step': '0.01'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = User.objects.filter(
            employee_profile__is_active=True
        ).order_by('first_name', 'last_name')
        self.fields['leave_type'].queryset = LeaveType.objects.filter(is_active=True)
        self.fields['year'].initial = date.today().year
    
    def clean(self):
        cleaned_data = super().clean()
        allocated_balance = cleaned_data.get('allocated_balance', 0)
        taken_balance = cleaned_data.get('taken_balance', 0)
        
        if taken_balance > allocated_balance:
            raise ValidationError('Le solde pris ne peut pas dépasser le solde alloué.')
        
        return cleaned_data


class LeaveTypeForm(forms.ModelForm):
    """
    Formulaire pour la création/modification des types de congés.
    """
    
    class Meta:
        model = LeaveType
        fields = [
            'name', 'description', 'allocation_amount', 'unit', 
            'allocation_type', 'max_consecutive_days', 'requires_justification',
            'requires_medical_certificate', 'advance_notice_days', 'is_paid', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Nom du type de congé'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Description du type de congé'
            }),
            'allocation_amount': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0'
            }),
            'unit': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'allocation_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'max_consecutive_days': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '1'
            }),
            'requires_justification': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
            'requires_medical_certificate': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
            'advance_notice_days': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0'
            }),
            'is_paid': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'
            })
        }
    
    def clean_allocation_amount(self):
        allocation_amount = self.cleaned_data.get('allocation_amount')
        if allocation_amount is not None and allocation_amount < 0:
            raise ValidationError('Le nombre de jours alloués ne peut pas être négatif.')
        return allocation_amount
    
    def clean_max_consecutive_days(self):
        max_consecutive_days = self.cleaned_data.get('max_consecutive_days')
        allocation_amount = self.cleaned_data.get('allocation_amount')
        
        if max_consecutive_days and allocation_amount:
            if max_consecutive_days > allocation_amount:
                raise ValidationError('Le nombre maximum de jours consécutifs ne peut pas dépasser l\'allocation annuelle.')
        
        return max_consecutive_days
