"""
Middleware pour rediriger automatiquement les admins vers Django Admin
"""
from django.shortcuts import redirect
from django.contrib import messages

class AdminRedirectMiddleware:
    """
    Middleware qui intercepte toutes les requêtes des admins
    et les redirige vers Django Admin
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Vérifier si l'utilisateur est connecté et est superuser (admin technique)
        if (request.user.is_authenticated and request.user.is_superuser):
            
            # URLs autorisées pour les admins (Django Admin uniquement - sécurité stricte)
            admin_allowed_paths = [
                '/admin/',
                '/admin',
                '/admin/logout/',
                '/admin/login/',
                '/accounts/logout/',  # Permettre la déconnexion
            ]
            
            # Si l'admin essaie d'accéder à une page du site web
            if not any(request.path.startswith(path) for path in admin_allowed_paths):
                try:
                    messages.info(request, 'Accès admin redirigé vers Django Admin.')
                except:
                    pass
                return redirect('/admin/')
        
        response = self.get_response(request)
        return response
