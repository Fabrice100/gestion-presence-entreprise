"""
Middleware pour forcer le changement de mot de passe à la première connexion.

Ce middleware vérifie si l'utilisateur a le flag force_password_change=True
et le redirige automatiquement vers la page de changement de mot de passe.

Conforme aux spécifications: MODULE 3 - Création de Compte Sécurisée
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class ForcePasswordChangeMiddleware:
    """
    Middleware forçant le changement de mot de passe pour les nouveaux comptes.
    
    Fonctionnement:
    1. Vérifie si l'utilisateur est authentifié
    2. Vérifie si force_password_change=True dans son EmployeeProfile
    3. Redirige vers /accounts/force-password-change/ si nécessaire
    4. Permet l'accès à certaines URLs (logout, changement MDP, static, etc.)
    """
    
    def __init__(self, get_response):
        """
        Initialise le middleware.
        
        Args:
            get_response: Callable pour obtenir la réponse
        """
        self.get_response = get_response
        
        # URLs autorisées même si force_password_change=True
        self.allowed_paths = [
            '/accounts/force-password-change/',
            '/accounts/logout/',
            '/accounts/password-changed/',
            '/static/',
            '/media/',
            '/admin/jsi18n/',  # Pour l'admin Django
        ]
    
    def __call__(self, request):
        """
        Traite chaque requête.
        
        Args:
            request: Objet HttpRequest
            
        Returns:
            HttpResponse
        """
        # 1. Vérifier si l'utilisateur est authentifié
        if request.user.is_authenticated:
            
            # 2. Vérifier s'il a un EmployeeProfile avec force_password_change=True
            if hasattr(request.user, 'employee_profile'):
                profile = request.user.employee_profile
                
                if profile.force_password_change:
                    # 3. Vérifier si la requête n'est pas vers une URL autorisée
                    current_path = request.path
                    
                    # Autoriser certaines URLs
                    if any(current_path.startswith(allowed) for allowed in self.allowed_paths):
                        return self.get_response(request)
                    
                    # 4. Rediriger vers la page de changement de mot de passe (namespaced)
                    force_change_url = reverse('accounts:force_password_change')
                    
                    # Éviter boucle infinie si déjà sur la page
                    if current_path != force_change_url:
                        messages.warning(
                            request,
                            "Pour des raisons de sécurité, vous devez changer votre mot de passe temporaire."
                        )
                        return redirect(force_change_url)
        
        # Continuer normalement
        return self.get_response(request)
