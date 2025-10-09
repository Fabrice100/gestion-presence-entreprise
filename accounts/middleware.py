"""
Middleware pour la gestion des utilisateurs.

Ce module contient les middleware pour :
- Forcer le changement de mot de passe à la première connexion
- Rediriger les utilisateurs vers les pages appropriées

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class ForcePasswordChangeMiddleware:
    """
    Middleware qui force les utilisateurs à changer leur mot de passe
    si le flag force_password_change est activé.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # URLs exemptées de la redirection
        exempt_urls = [
            reverse('accounts:password_change'),
            reverse('accounts:password_change_done'),
            reverse('accounts:exit'),
            reverse('accounts:logout'),
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        # Vérifier si l'utilisateur est connecté
        if request.user.is_authenticated:
            # Vérifier si l'utilisateur a un profil employé
            if hasattr(request.user, 'employee_profile'):
                profile = request.user.employee_profile
                
                # Si le changement de mot de passe est requis
                if profile.force_password_change:
                    # Vérifier si l'URL actuelle n'est pas exemptée
                    current_path = request.path
                    is_exempt = any(current_path.startswith(url) for url in exempt_urls)
                    
                    if not is_exempt:
                        # Ajouter un message informatif
                        messages.warning(
                            request,
                            'Vous devez changer votre mot de passe avant de continuer.'
                        )
                        # Rediriger vers la page de changement de mot de passe
                        return redirect('accounts:password_change')
        
        response = self.get_response(request)
        return response

