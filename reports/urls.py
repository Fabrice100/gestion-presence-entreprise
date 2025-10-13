"""
URLs pour l'application reports (rapports et exports).

Ce module définit les routes pour :
- Génération de rapports avancés
- Export de données en PDF/Excel
- Tableaux de bord analytiques
- Paramètres système

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.urls import path
from . import views
from . import report_views

app_name = 'reports'

urlpatterns = [
    # Tableau de bord des rapports
    path('', report_views.ReportsDashboardView.as_view(), name='reports_dashboard'),
    
    # Rapports détaillés
    path('attendance/', report_views.AttendanceReportView.as_view(), name='attendance_report'),
    path('leave/', report_views.LeaveReportView.as_view(), name='leave_report'),
    path('anomalies/', report_views.AnomalyReportView.as_view(), name='anomaly_report'),
    
    # API pour exports
    path('api/export/', report_views.export_report_api, name='export_report_api'),
    
    # API pour statistiques critiques
    path('api/critical-stats/', report_views.critical_stats_api, name='critical_stats_api'),
    
    # Paramètres système
    path('settings/', views.SystemSettingsView.as_view(), name='system_settings'),
    
    # Templates de rapports
    path('templates/', views.ReportTemplateListView.as_view(), name='report_template_list'),
]