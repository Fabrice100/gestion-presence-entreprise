"""
Formulaires pour l'application accounts.

Ce module contient les formulaires pour :
- Création et modification des départements
- Création et modification des utilisateurs
- Gestion des profils employés

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import EmployeeProfile, Department, WorkSchedule


class ManagerChoiceField(forms.ModelChoiceField):
    """
    Affiche le nom complet du manager dans les listes déroulantes
    au lieu du username par défaut.
    """
    def label_from_instance(self, obj):  # pragma: no cover - simple présentation
        full_name = (obj.get_full_name() or '').strip()
        return full_name if full_name else obj.username


class DepartmentForm(forms.ModelForm):
    """
    Formulaire pour la création/modification d'un département.
    """
    
    class Meta:
        model = Department
        fields = ['name', 'description', 'manager', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'Nom du département'
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'rows': 3,
                'placeholder': 'Description du département'
            }),
            'manager': forms.Select(attrs={
                'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary-600 border-gray-300 rounded'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remplacer le champ pour afficher le nom complet
        current_widget = self.fields['manager'].widget
        self.fields['manager'] = ManagerChoiceField(
            queryset=User.objects.none(),
            required=False,
            widget=current_widget,
            empty_label=None,
        )

        # Filtrer les managers actifs
        self.fields['manager'].queryset = User.objects.filter(
            employee_profile__role='manager',
            employee_profile__is_active=True
        )
        self.fields['manager'].empty_label = "Aucun manager"


class EmployeeCreateFormSimple(forms.ModelForm):
    """
    Formulaire simplifié pour la création d'un employé (sans mot de passe).
    Le mot de passe sera généré automatiquement et envoyé par email.
    """
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Email professionnel',
            'required': 'required'
        }),
        help_text='Un email avec les identifiants sera envoyé à cette adresse'
    )
    
    first_name = forms.CharField(
        required=True,
        max_length=30,
        min_length=2,
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Prénom',
            'required': 'required',
            'pattern': r'[A-Za-zÀ-ÿ\s\-]+',
            'title': 'Le prénom ne doit contenir que des lettres (minimum 2 caractères)'
        })
    )
    
    last_name = forms.CharField(
        required=True,
        max_length=30,
        min_length=2,
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Nom',
            'required': 'required',
            'pattern': r'[A-Za-zÀ-ÿ\s\-]+',
            'title': 'Le nom ne doit contenir que des lettres (minimum 2 caractères)'
        })
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        empty_label="Sélectionner un département",
        required=True,
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'required': 'required'
        })
    )
    
    manager = ManagerChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="Aucun manager",
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
        })
    )
    
    current_work_schedule = forms.ModelChoiceField(
        queryset=WorkSchedule.objects.all(),
        required=False,
        empty_label="Sélectionner un profil horaire",
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
        }),
        help_text='Profil horaire à assigner à cet employé. Si aucun n\'est sélectionné, le profil par défaut sera utilisé.'
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']
        # Le username sera généré automatiquement
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les managers actifs pour le champ manager
        self.fields['manager'].queryset = User.objects.filter(
            employee_profile__role='manager',
            employee_profile__is_active=True
        )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Cet email est déjà utilisé.')
        return email
    
    def clean_first_name(self):
        """Valide que le prénom ne contient que des lettres."""
        import re
        first_name = self.cleaned_data.get('first_name', '').strip()
        
        if not first_name:
            raise ValidationError('Le prénom est obligatoire.')
        
        if len(first_name) < 2:
            raise ValidationError('Le prénom doit contenir au moins 2 caractères.')
        
        # Vérifier que le prénom ne contient que des lettres, espaces et tirets
        if not re.match(r'^[A-Za-zÀ-ÿ\s\-]+$', first_name):
            raise ValidationError('Le prénom ne doit contenir que des lettres.')
        
        # Vérifier qu'il n'y a pas que des chiffres
        if first_name.isdigit():
            raise ValidationError('Le prénom ne peut pas être composé uniquement de chiffres.')
        
        return first_name.title()  # Capitaliser la première lettre
    
    def clean_last_name(self):
        """Valide que le nom ne contient que des lettres."""
        import re
        last_name = self.cleaned_data.get('last_name', '').strip()
        
        if not last_name:
            raise ValidationError('Le nom est obligatoire.')
        
        if len(last_name) < 2:
            raise ValidationError('Le nom doit contenir au moins 2 caractères.')
        
        # Vérifier que le nom ne contient que des lettres, espaces et tirets
        if not re.match(r'^[A-Za-zÀ-ÿ\s\-]+$', last_name):
            raise ValidationError('Le nom ne doit contenir que des lettres.')
        
        # Vérifier qu'il n'y a pas que des chiffres
        if last_name.isdigit():
            raise ValidationError('Le nom ne peut pas être composé uniquement de chiffres.')
        
        return last_name.upper()  # Mettre en majuscules


class EmployeeProfileForm(forms.ModelForm):
    """
    Formulaire pour la modification d'un profil employé.
    """
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'department', 'manager', 'role', 'employee_type', 
            'hire_date', 'contract_end_date', 
            'current_work_schedule',
            'is_active', 'can_punch'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500'}),
            'manager': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500'}),
            'role': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500'}),
            'employee_type': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500'}),
            'hire_date': forms.DateInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500', 'type': 'date'}),
            'current_work_schedule': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-primary-600 border-gray-300 rounded'}),
            'can_punch': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-primary-600 border-gray-300 rounded'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les départements actifs
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
        self.fields['department'].empty_label = "Aucun département"
        
        # Remplacer le champ manager pour afficher le nom complet
        current_widget = self.fields['manager'].widget
        required = self.fields['manager'].required
        self.fields['manager'] = ManagerChoiceField(
            queryset=User.objects.none(),
            required=required,
            widget=current_widget,
            empty_label=None,
        )
        # Filtrer les managers actifs
        self.fields['manager'].queryset = User.objects.filter(
            employee_profile__role='manager',
            employee_profile__is_active=True
        )
        self.fields['manager'].empty_label = "Aucun manager"
        
        # Configuration du champ profil horaire
        self.fields['current_work_schedule'].queryset = WorkSchedule.objects.all()
        self.fields['current_work_schedule'].empty_label = "Profil par défaut"
        self.fields['current_work_schedule'].help_text = (
            "Profil horaire contractuel de l'employé. "
            "Si aucun n'est sélectionné, le profil par défaut sera utilisé."
        )


class UserSearchForm(forms.Form):
    """
    Formulaire de recherche d'utilisateurs.
    """
    
    search = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
            'placeholder': 'Rechercher par nom, email ou ID employé...'
        })
    )
    
    role = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous les rôles')] + EmployeeProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500'})
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label="Tous les départements",
        widget=forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500'})
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous'), ('true', 'Actif'), ('false', 'Inactif')],
        widget=forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 px-3 py-2 bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500'})
    )
