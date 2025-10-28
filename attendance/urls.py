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
from . import anomaly_views

app_name = 'attendance'

urlpatterns = [
    # Configuration système
    path('settings/', settings_views.CompanySettingsView.as_view(), name='company_settings'),
    
    # Pointage
    path('punch/', views.PunchView.as_view(), {'template_name': 'attendance/punch_smart.html'}, name='punch'),
    path('punch/original/', views.PunchView.as_view(), name='punch_original'),
    path('punch/gps-test/', TemplateView.as_view(template_name='attendance/gps_test.html'), name='gps_test'),
    path('punch/demo/', views.PunchView.as_view(), {'template_name': 'attendance/punch_demo.html'}, name='punch_demo'),
    path('punch/test/', views.PunchView.as_view(), {'template_name': 'attendance/punch_test.html'}, name='punch_test'),
    
    # Consultation des présences
    path('my-attendance/', views.MyAttendanceView.as_view(), name='my_attendance'),
    path('team-attendance/', views.TeamAttendanceView.as_view(), name='team_attendance'),
    path('anomalies/', views.AnomaliesManagementView.as_view(), name='anomalies'),
    
    # === TASK 6: Gestion des anomalies (Manager + RH) ===
    # Manager: anomalies de son département
    path('anomalies/manager/', anomaly_views.ManagerAnomalyListView.as_view(), name='manager_anomaly_list'),
    
    # RH: toutes les anomalies (vue globale)
    path('anomalies/rh/', anomaly_views.RHAnomalyListView.as_view(), name='rh_anomaly_list'),
    
    # Détails d'une anomalie
    path('anomalies/<int:pk>/', anomaly_views.AnomalyDetailView.as_view(), name='anomaly_detail'),
    
    # Résolution d'une anomalie (POST)
    path('anomalies/<int:pk>/resolve/', anomaly_views.AnomalyResolutionView.as_view(), name='resolve_anomaly'),
    
    
    # Diagnostic GPS
    path('gps-diagnostic/', TemplateView.as_view(template_name='attendance/gps_diagnostic.html'), name='gps_diagnostic'),
    path('test-gps/', TemplateView.as_view(template_name='attendance/test_gps.html'), name='test_gps'),

]
