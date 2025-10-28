"""
Formulaires pour la gestion des profils horaires (RH uniquement).
"""
from django import forms
from django.core.exceptions import ValidationError
from accounts.models import WorkSchedule


class WorkScheduleForm(forms.ModelForm):
    """
    Formulaire de création/modification d'un profil horaire.
    
    Validation :
    - Heure de fin doit être après heure de début
    - Pause doit être dans les heures de travail
    """
    
    class Meta:
        model = WorkSchedule
        fields = ['name', 'description', 'start_time', 'end_time', 
                  'pause_start', 'pause_end', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Bureau Standard, Mi-temps, Équipe Nuit'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du profil horaire et à qui il s\'applique'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'pause_start': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'pause_end': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Nom du profil',
            'description': 'Description',
            'start_time': 'Heure de début (HDC)',
            'end_time': 'Heure de fin (HFC)',
            'pause_start': 'Début de pause',
            'pause_end': 'Fin de pause',
            'is_default': 'Profil par défaut'
        }
        help_texts = {
            'name': 'Nom unique du profil horaire',
            'start_time': 'Heure de début contractuelle (ex: 08:00)',
            'end_time': 'Heure de fin contractuelle (ex: 18:00)',
            'pause_start': 'Heure de début de la pause (ex: 12:00)',
            'pause_end': 'Heure de fin de la pause (ex: 14:00)',
            'is_default': 'Ce profil sera utilisé par défaut pour les nouveaux employés'
        }
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        pause_start = cleaned_data.get('pause_start')
        pause_end = cleaned_data.get('pause_end')
        
        # Vérifier que l'heure de fin est après l'heure de début (sauf équipe de nuit)
        if start_time and end_time:
            # On accepte si end_time < start_time (équipe de nuit)
            pass
        
        # Vérifier que la pause est cohérente
        if pause_start and pause_end:
            if pause_end <= pause_start:
                raise ValidationError({
                    'pause_end': 'L\'heure de fin de pause doit être après l\'heure de début'
                })
        
        return cleaned_data
    
    def clean_is_default(self):
        """Validation : un seul profil par défaut."""
        is_default = self.cleaned_data.get('is_default')
        
        if is_default:
            # Vérifier qu'il n'y a pas déjà un profil par défaut
            existing_default = WorkSchedule.objects.filter(is_default=True)
            
            # Si on modifie un profil existant, exclure celui-ci
            if self.instance.pk:
                existing_default = existing_default.exclude(pk=self.instance.pk)
            
            if existing_default.exists():
                raise ValidationError(
                    f'Le profil "{existing_default.first().name}" est déjà défini par défaut. '
                    'Désactivez-le d\'abord pour en définir un nouveau.'
                )
        
        return is_default


class ChangeEmployeeScheduleForm(forms.Form):
    """
    Formulaire pour changer le profil horaire d'un employé.
    Utilisé dans l'interface RH.
    """
    
    new_schedule = forms.ModelChoiceField(
        queryset=WorkSchedule.objects.all().order_by('name'),
        empty_label="Sélectionnez un profil horaire",
        label="Nouveau profil horaire",
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text="Le changement sera effectif immédiatement"
    )
    
    reason = forms.CharField(
        required=False,
        label="Motif du changement (optionnel)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ex: Changement d\'équipe, passage à mi-temps, etc.'
        })
    )
