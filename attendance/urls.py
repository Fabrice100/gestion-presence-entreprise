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
# from . import overtime_views  # Temporairement désactivé
from . import settings_views

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
    path('punch/in/', views.PunchInView.as_view(), name='punch_in'),
    path('punch/out/', views.PunchOutView.as_view(), name='punch_out'),
    
    # Consultation des présences
    path('my-attendance/', views.MyAttendanceView.as_view(), name='my_attendance'),
    
    # API pour le pointage (AJAX)
    path('api/punch/', views.PunchAPIView.as_view(), name='punch_api'),
    
    # Diagnostic GPS
    path('gps-diagnostic/', TemplateView.as_view(template_name='attendance/gps_diagnostic.html'), name='gps_diagnostic'),
    path('test-gps/', TemplateView.as_view(template_name='attendance/test_gps.html'), name='test_gps'),

    # Heures supplémentaires (temporairement désactivé)
    # path('overtime/', overtime_views.OvertimeRecordListView.as_view(), name='overtime_record_list'),
    # path('overtime/<int:pk>/', overtime_views.OvertimeRecordDetailView.as_view(), name='overtime_record_detail'),
    # path('overtime/approvals/', overtime_views.OvertimeApprovalListView.as_view(), name='overtime_approval_list'),
    # path('overtime/<int:pk>/approve/', overtime_views.OvertimeApprovalProcessView.as_view(), name='overtime_approval_process'),

    # API pour les heures supplémentaires
    # path('api/overtime/stats/', overtime_views.get_overtime_stats_api, name='api_overtime_stats'),
    
    # Interface RH - Gestion des anomalies
    path('rh/anomalies/', views.rh_anomalies_list, name='rh_anomalies_list'),
    path('rh/anomalies/corriger/<int:anomaly_id>/', views.rh_anomaly_correct, name='rh_anomaly_correct'),
    path('rh/anomalies/ignorer/<int:anomaly_id>/', views.rh_anomaly_ignore, name='rh_anomaly_ignore'),
    path('rh/anomalies/export/', views.rh_anomalies_export_csv, name='rh_anomalies_export'),
]
