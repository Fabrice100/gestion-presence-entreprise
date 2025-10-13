"""
Backend d'authentification personnalisé pour le système de gestion de présence.

Ce backend permet aux employés de se connecter avec leur ID Employé (EMP001, MGR001, etc.)
au lieu du username Django.

Auteur: Système de Gestion de Présence
Version: 1.0
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from accounts.models import EmployeeProfile


class EmployeeIDBackend(ModelBackend):
    """
    Backend d'authentification personnalisé qui permet la connexion avec l'ID Employé.
    
    L'utilisateur peut se connecter avec :
    - Son ID Employé (EMP001, MGR001, RH001, etc.) + mot de passe
    - Ou son username classique + mot de passe (fallback)
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authentifie un utilisateur avec son ID Employé ou son username.
        
        Args:
            request: La requête HTTP
            username: L'ID Employé ou le username
            password: Le mot de passe
            
        Returns:
            User: L'utilisateur authentifié ou None
        """
        if username is None or password is None:
            return None
        
        try:
            # Essayer d'abord de trouver par employee_id
            try:
                profile = EmployeeProfile.objects.select_related('user').get(employee_id=username)
                user = profile.user
            except EmployeeProfile.DoesNotExist:
                # Fallback: essayer avec le username classique
                user = User.objects.get(username=username)
            
            # Vérifier le mot de passe
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
                
        except User.DoesNotExist:
            # Exécuter le hashage par défaut pour éviter les attaques de timing
            User().set_password(password)
            return None
        
        return None




