"""
URLs pour l'application attendance (pointage et présence).

Ce module définit les routes pour :
- Pointage d'entrée et de sortie
- Consultation des présences
- Gestion des anomalies
- Rapports de présence

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Pointage
    path('punch/', views.PunchView.as_view(), name='punch'),
    path('punch/in/', views.PunchInView.as_view(), name='punch_in'),
    path('punch/out/', views.PunchOutView.as_view(), name='punch_out'),
    
    # Consultation des présences
    path('my-attendance/', views.MyAttendanceView.as_view(), name='my_attendance'),
    
    # API pour le pointage (AJAX)
    path('api/punch/', views.PunchAPIView.as_view(), name='punch_api'),
]
