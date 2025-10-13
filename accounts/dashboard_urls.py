"""
URLs pour les tableaux de bord par rôle.

Ce module définit les routes pour les différents tableaux de bord :
- Dashboard général (redirection selon le rôle)
- Dashboard employé
- Dashboard manager
- Dashboard RH/DG
- Admin redirigé vers Django Admin (/admin/)

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.urls import path
from . import dashboard_views

app_name = 'dashboard'

urlpatterns = [
    # Tableau de bord principal (redirection selon le rôle)
    path('', dashboard_views.DashboardView.as_view(), name='dashboard'),
    
    # Tableaux de bord spécifiques par rôle
    path('admin/', dashboard_views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('employee/', dashboard_views.EmployeeDashboardView.as_view(), name='employee_dashboard'),
    path('manager/', dashboard_views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('rh-dg/', dashboard_views.RHDGDashboardView.as_view(), name='rh_dg_dashboard'),
]


