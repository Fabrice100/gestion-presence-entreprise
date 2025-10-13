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
from . import views
from . import overtime_views
from . import settings_views

app_name = 'attendance'

urlpatterns = [
    # Configuration système
    path('settings/', settings_views.CompanySettingsView.as_view(), name='company_settings'),
    
    # Pointage
    path('punch/', views.PunchView.as_view(), name='punch'),
    path('punch/in/', views.PunchInView.as_view(), name='punch_in'),
    path('punch/out/', views.PunchOutView.as_view(), name='punch_out'),
    
    # Consultation des présences
    path('my-attendance/', views.MyAttendanceView.as_view(), name='my_attendance'),
    
    # API pour le pointage (AJAX)
    path('api/punch/', views.PunchAPIView.as_view(), name='punch_api'),

    # Heures supplémentaires
    path('overtime/', overtime_views.OvertimeRecordListView.as_view(), name='overtime_record_list'),
    path('overtime/<int:pk>/', overtime_views.OvertimeRecordDetailView.as_view(), name='overtime_record_detail'),
    path('overtime/approvals/', overtime_views.OvertimeApprovalListView.as_view(), name='overtime_approval_list'),
    path('overtime/<int:pk>/approve/', overtime_views.OvertimeApprovalProcessView.as_view(), name='overtime_approval_process'),

    # API pour les heures supplémentaires
    path('api/overtime/stats/', overtime_views.get_overtime_stats_api, name='api_overtime_stats'),
]
