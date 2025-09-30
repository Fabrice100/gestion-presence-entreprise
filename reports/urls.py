"""
URLs pour l'application reports (rapports et paramètres).

Ce module définit les routes pour :
- Génération de rapports
- Gestion des paramètres système
- Modèles de rapports

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Rapports généraux
    path('', views.ReportListView.as_view(), name='report_list'),
    path('attendance/', views.AttendanceReportView.as_view(), name='attendance_report'),
    path('leave/', views.LeaveReportView.as_view(), name='leave_report'),
    path('summary/', views.SummaryReportView.as_view(), name='summary_report'),
    
    # Génération de rapports
    path('generate/<str:report_type>/', views.ReportGenerateView.as_view(), name='report_generate'),
    path('download/<int:pk>/', views.ReportDownloadView.as_view(), name='report_download'),
    
    # Paramètres système (admin seulement)
    path('settings/', views.SystemSettingsView.as_view(), name='system_settings'),
    path('settings/<str:key>/edit/', views.SystemSettingEditView.as_view(), name='setting_edit'),
    
    # Modèles de rapports
    path('templates/', views.ReportTemplateListView.as_view(), name='report_template_list'),
    path('templates/<int:pk>/', views.ReportTemplateDetailView.as_view(), name='report_template_detail'),
    path('templates/create/', views.ReportTemplateCreateView.as_view(), name='report_template_create'),
]

