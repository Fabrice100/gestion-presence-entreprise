"""
URLs pour l'application accounts (authentification et gestion des comptes).

Ce module définit les routes pour :
- Authentification (login, logout, password)
- Gestion des profils utilisateurs
- Inscription et activation des comptes

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .logout_view import logout_view
from .force_password_views import ForcePasswordChangeView, password_changed_success

app_name = 'accounts'

urlpatterns = [
    # Authentification
    path('login/', views.CustomLoginView.as_view(), name='login'),
    
    path('logout/', logout_view, name='logout'),
    path('exit/', logout_view, name='exit'),
    
    # Gestion des mots de passe (templates créés)
    path('password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
    
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html'
    ), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Changement de mot de passe forcé (nouveau compte)
    path('force-password-change/', ForcePasswordChangeView.as_view(), name='force_password_change'),
    path('password-changed/', password_changed_success, name='password_changed_success'),
    
    # Profil utilisateur
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
]

