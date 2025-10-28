"""
Mixins d'authentification et de permissions centralisés.

Ce module respecte les principes SOLID :
- Single Responsibility : Chaque mixin a une responsabilité claire
- Open/Closed : Extensible sans modification
- Liskov Substitution : Les mixins sont substituables
- Interface Segregation : Interfaces spécialisées
- Dependency Inversion : Dépendance vers des abstractions

Auteur: Système de Gestion de Présence
Version: 2.0 (Refactorisé)
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin as DjangoLoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
import logging

logger = logging.getLogger(__name__)


class BasePermissionMixin:
    """
    Mixin de base pour toutes les vérifications de permissions.
    
    Respecte le Single Responsibility Principle en ne gérant que
    la logique commune de permissions.
    """
    
    def handle_no_permission(self):
        """
        Gère le cas où l'utilisateur n'a pas les permissions.
        
        Peut être surchargé par les classes filles pour personnaliser
        le comportement (Open/Closed Principle).
        """
        if not self.request.user.is_authenticated:
            return redirect('accounts:login')
        
        messages.error(
            self.request,
            self.get_permission_denied_message()
        )
        return redirect('dashboard:dashboard')
    
    def get_permission_denied_message(self):
        """
        Message d'erreur personnalisable pour chaque type de permission.
        """
        return "Vous n'avez pas les permissions nécessaires pour accéder à cette page."


class EnhancedLoginRequiredMixin(BasePermissionMixin, DjangoLoginRequiredMixin):
    """
    Mixin d'authentification unifié et amélioré.
    
    Respecte le Liskov Substitution Principle en étant un remplacement
    direct de tous les LoginRequiredMixin personnalisés existants.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """
        Vérifie l'authentification avec logging de sécurité.
        """
        if not request.user.is_authenticated:
            logger.warning(
                f"Tentative d'accès non authentifié à {request.path} "
                f"depuis {self.get_client_ip(request)}"
            )
            return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_client_ip(self, request):
        """Récupère l'IP du client pour les logs de sécurité."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class EmployeeRequiredMixin(BasePermissionMixin, UserPassesTestMixin):
    """
    Mixin pour vérifier que l'utilisateur est un employé actif.
    
    Interface Segregation Principle : Séparation des préoccupations
    entre authentification et vérification du statut employé.
    """
    
    def test_func(self):
        """
        Teste si l'utilisateur est un employé actif.
        IMPORTANT: Les superusers Django sont uniquement pour /admin/ (configuration technique).
        Les fonctionnalités métier nécessitent un EmployeeProfile avec un rôle (rh, manager, employee).
        """
        if not self.request.user.is_authenticated:
            return False
        
        # Rejeter les superusers Django (ils doivent utiliser uniquement /admin/)
        if self.request.user.is_superuser:
            logger.error(
                f"Superuser Django {self.request.user.username} tentant d'accéder à {self.request.path}. "
                f"Les superusers sont uniquement pour /admin/. Utilisez un compte avec EmployeeProfile."
            )
            return False
        
        if not hasattr(self.request.user, 'employee_profile'):
            logger.error(
                f"Utilisateur {self.request.user.username} sans profil employé "
                f"tentant d'accéder à {self.request.path}"
            )
            return False
        
        return self.request.user.employee_profile.is_active
    
    def get_permission_denied_message(self):
        return "Votre profil employé est requis pour accéder à cette fonctionnalité."


class ManagerRequiredMixin(EmployeeRequiredMixin):
    """
    Mixin pour vérifier que l'utilisateur est un manager.
    
    Hérite d'EmployeeRequiredMixin (Dependency Inversion Principle).
    """
    
    def test_func(self):
        """
        Teste si l'utilisateur est un manager actif.
        """
        if not super().test_func():
            return False
        
        return self.request.user.employee_profile.is_manager()
    
    def get_permission_denied_message(self):
        return "Seuls les managers peuvent accéder à cette fonctionnalité."


class RHRequiredMixin(EmployeeRequiredMixin):
    """
    Mixin pour vérifier que l'utilisateur est RH.
    """
    
    def test_func(self):
        """
        Teste si l'utilisateur est RH.
        """
        if not super().test_func():
            return False
        
        return self.request.user.employee_profile.is_rh()
    
    def get_permission_denied_message(self):
        return "Seuls les RH peuvent accéder à cette fonctionnalité."


class AdminRequiredMixin(EmployeeRequiredMixin):
    """
    Mixin pour vérifier que l'utilisateur est administrateur.
    """
    
    def test_func(self):
        """
        Teste si l'utilisateur est administrateur.
        """
        if not super().test_func():
            return False
        
        # Seul le superuser Django peut accéder (pas de rôle métier 'admin')
        return self.request.user.is_superuser
    
    def get_permission_denied_message(self):
        return "Seuls les administrateurs techniques (superuser Django) peuvent accéder à cette fonctionnalité."


class OwnerOrManagerRequiredMixin(EmployeeRequiredMixin):
    """
    Mixin pour vérifier que l'utilisateur est propriétaire de l'objet ou manager.
    
    Utile pour les vues de détail où un employé peut voir ses propres données
    ou un manager peut voir les données de son équipe.
    """
    
    def test_func(self):
        """
        Teste si l'utilisateur peut accéder à l'objet.
        """
        if not super().test_func():
            return False
        
        # Si c'est un manager ou RH, accès autorisé
        if (self.request.user.employee_profile.is_manager() or 
            self.request.user.employee_profile.is_rh()):
            return True
        
        # Sinon, vérifier si c'est le propriétaire
        obj = self.get_object()
        return self.is_owner(obj)
    
    def is_owner(self, obj):
        """
        Méthode à surcharger pour définir la logique de propriété.
        
        Args:
            obj: L'objet à vérifier
            
        Returns:
            bool: True si l'utilisateur est propriétaire
        """
        # Logique par défaut : vérifier si obj.employee == user
        if hasattr(obj, 'employee'):
            return obj.employee == self.request.user
        elif hasattr(obj, 'user'):
            return obj.user == self.request.user
        
        return False
    
    def get_permission_denied_message(self):
        return "Vous ne pouvez accéder qu'à vos propres données."


# Décorateur pour les vues fonction (alternative aux mixins)
def employee_required(view_func):
    """
    Décorateur pour exiger qu'un utilisateur soit un employé actif.
    
    Usage:
        @employee_required
        def my_view(request):
            # Vue accessible aux employés seulement
    """
    @method_decorator(login_required)
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'employee_profile'):
            messages.error(request, 'Profil employé requis.')
            return redirect('dashboard:dashboard')
        
        if not request.user.employee_profile.is_active:
            messages.error(request, 'Votre compte employé est inactif.')
            return redirect('dashboard:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view


def manager_required(view_func):
    """
    Décorateur pour exiger qu'un utilisateur soit un manager.
    """
    @employee_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.employee_profile.is_manager():
            messages.error(request, 'Seuls les managers peuvent accéder à cette fonctionnalité.')
            return redirect('dashboard:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view


def rh_required(view_func):
    """
    Décorateur pour exiger qu'un utilisateur soit RH.
    """
    @employee_required
    def wrapped_view(request, *args, **kwargs):
        if not request.user.employee_profile.is_rh():
            messages.error(request, 'Seuls les RH peuvent accéder à cette fonctionnalité.')
            return redirect('dashboard:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view


# Alias pour la compatibilité avec l'ancien code
LoginRequiredMixin = EnhancedLoginRequiredMixin