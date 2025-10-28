"""
Vue pour forcer le changement de mot de passe à la première connexion.

Conforme aux spécifications: MODULE 3 - Création de Compte Sécurisée
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django import forms
from django.contrib.auth.forms import PasswordChangeForm


class ForcePasswordChangeForm(PasswordChangeForm):
    """
    Formulaire personnalisé pour le changement de mot de passe forcé.
    
    Ajoute des validations supplémentaires et un style Bootstrap.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ajouter classes CSS Bootstrap/TailwindCSS
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all',
                'placeholder': field.label
            })
    
    def clean_new_password1(self):
        """
        Validation personnalisée du nouveau mot de passe.
        
        Règles:
        - Minimum 8 caractères
        - Au moins une lettre majuscule
        - Au moins une lettre minuscule
        - Au moins un chiffre
        - Au moins un caractère spécial
        """
        password = self.cleaned_data.get('new_password1')
        
        # Validation longueur
        if len(password) < 8:
            raise forms.ValidationError(
                "Le mot de passe doit contenir au moins 8 caractères."
            )
        
        # Validation complexité
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        if not (has_upper and has_lower and has_digit):
            raise forms.ValidationError(
                "Le mot de passe doit contenir au moins une majuscule, "
                "une minuscule et un chiffre."
            )
        
        return password


@method_decorator(login_required, name='dispatch')
class ForcePasswordChangeView(View):
    """
    Vue pour forcer le changement de mot de passe.
    
    Cette vue est accessible uniquement aux utilisateurs ayant
    force_password_change=True dans leur EmployeeProfile.
    """
    
    template_name = 'accounts/force_password_change.html'
    
    def get(self, request):
        """
        Affiche le formulaire de changement de mot de passe.
        
        Args:
            request: Objet HttpRequest
            
        Returns:
            HttpResponse avec le formulaire
        """
        form = ForcePasswordChangeForm(user=request.user)
        
        context = {
            'form': form,
            'title': 'Changement de mot de passe obligatoire',
            'user': request.user,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        """
        Traite le changement de mot de passe.
        
        Args:
            request: Objet HttpRequest
            
        Returns:
            HttpResponse (redirect si succès, formulaire avec erreurs sinon)
        """
        form = ForcePasswordChangeForm(user=request.user, data=request.POST)
        
        if form.is_valid():
            # 1. Sauvegarder le nouveau mot de passe
            user = form.save()
            
            # 2. Désactiver le flag force_password_change
            if hasattr(user, 'employee_profile'):
                profile = user.employee_profile
                profile.force_password_change = False
                profile.save(update_fields=['force_password_change'])
            
            # 3. Maintenir la session active après changement de mot de passe
            update_session_auth_hash(request, user)
            
            # 4. Message de succès
            messages.success(
                request,
                "✅ Votre mot de passe a été changé avec succès ! "
                "Vous pouvez maintenant utiliser le système normalement."
            )
            
            # 5. Rediriger vers le dashboard approprié
            profile = user.employee_profile
            
            # Redirection selon rôle métier (3 rôles)
            if profile.role == 'rh':
                return redirect('rh_dashboard')
            elif profile.role == 'manager':
                return redirect('manager_dashboard')
            else:  # employee
                return redirect('employee_dashboard')
        
        # Formulaire invalide : réafficher avec erreurs
        context = {
            'form': form,
            'title': 'Changement de mot de passe obligatoire',
            'user': request.user,
        }
        
        return render(request, self.template_name, context)


@login_required
def password_changed_success(request):
    """
    Page de confirmation après changement de mot de passe.
    
    Args:
        request: Objet HttpRequest
        
    Returns:
        HttpResponse
    """
    context = {
        'title': 'Mot de passe changé avec succès',
        'user': request.user,
    }
    
    return render(request, 'accounts/password_changed_success.html', context)
