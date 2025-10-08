"""
Vue de déconnexion simple et directe.
"""
from django.shortcuts import redirect
from django.contrib.auth import logout


def logout_view(request):
    """Déconnexion simple qui fonctionne toujours."""
    logout(request)
    return redirect('/accounts/login/')

