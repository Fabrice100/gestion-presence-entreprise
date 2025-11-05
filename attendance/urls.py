"""
URLs pour l'application attendance (pointage et présence).

Ce module définit les routes pour :
- Pointage d'entrée et de sortie
- Consultation des présences
- Gestion des anomalies
- Rapports de présence
- Heures supplémentaires

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.urls import path
from django.views.generic import TemplateView
from . import views
from . import settings_views

app_name = 'attendance'

urlpatterns = [
    # Configuration système
    path('settings/', settings_views.CompanySettingsView.as_view(), name='company_settings'),
    
    # Pointage
    path('punch/', views.PunchView.as_view(), name='punch'),
    
    # Consultation des présences
    path('my-attendance/', views.MyAttendanceView.as_view(), name='my_attendance'),
    path('team-attendance/', views.TeamAttendanceView.as_view(), name='team_attendance'),

]
