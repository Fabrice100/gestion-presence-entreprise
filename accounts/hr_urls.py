"""
URLs pour l'interface RH/DG.

Ce module définit les routes pour :
- Tableau de bord RH/DG
- Gestion des départements
- Gestion des utilisateurs (managers et employés)
- API pour la gestion dynamique

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.urls import path
from . import hr_views

app_name = 'hr'

urlpatterns = [
    # Tableau de bord RH/DG
    path('', hr_views.HRDashboardView.as_view(), name='hr_dashboard'),
    
    # Gestion des départements
    path('departments/', hr_views.DepartmentListView.as_view(), name='department_list'),
    path('departments/create/', hr_views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', hr_views.DepartmentUpdateView.as_view(), name='department_edit'),
    path('departments/<int:pk>/delete/', hr_views.DepartmentDeleteView.as_view(), name='department_delete'),
    
    # Gestion des utilisateurs
    path('users/', hr_views.UserListView.as_view(), name='user_list'),
    path('users/managers/create/', hr_views.ManagerCreateView.as_view(), name='manager_create'),
    path('users/employees/create/', hr_views.EmployeeCreateView.as_view(), name='employee_create'),
    path('users/<int:pk>/edit/', hr_views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', hr_views.UserDeleteView.as_view(), name='user_delete'),
    
    # API
    path('api/managers/', hr_views.get_managers_by_department, name='api_managers'),
]

