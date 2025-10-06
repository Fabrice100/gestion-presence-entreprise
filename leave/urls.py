"""
URLs pour l'application leave (congés et absences).

Ce module définit les routes pour :
- Demande de congés avec workflow de validation
- Validation des congés par managers et RH/DG
- Consultation des soldes
- Gestion des types de congés

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.urls import path
from . import views
from . import workflow_views

app_name = 'leave'

urlpatterns = [
    # Demandes de congés (workflow)
    path('requests/', workflow_views.LeaveRequestListView.as_view(), name='leave_request_list'),
    path('requests/create/', workflow_views.LeaveRequestCreateView.as_view(), name='leave_request_create'),
    
    # Validation des congés (workflow)
    path('approvals/', workflow_views.LeaveApprovalListView.as_view(), name='leave_approval_list'),
    path('approvals/<int:pk>/', workflow_views.LeaveApprovalDetailView.as_view(), name='leave_approval_detail'),
    path('approvals/<int:pk>/process/', workflow_views.LeaveApprovalUpdateView.as_view(), name='leave_approval_process'),
    
    # Soldes de congés
    path('balances/', workflow_views.LeaveBalanceListView.as_view(), name='leave_balance_list'),
    
    # Types de congés
    path('types/', views.LeaveTypeListView.as_view(), name='leave_type_list'),
    path('types/<int:pk>/', views.LeaveTypeDetailView.as_view(), name='leave_type_detail'),
    
    # Jours fériés
    path('holidays/', views.HolidayListView.as_view(), name='holiday_list'),
    path('holidays/<int:pk>/', views.HolidayDetailView.as_view(), name='holiday_detail'),
    
    # API
    path('api/statistics/', workflow_views.leave_statistics_api, name='leave_statistics_api'),
]