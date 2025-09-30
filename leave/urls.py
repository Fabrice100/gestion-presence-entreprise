"""
URLs pour l'application leave (congés et absences).

Ce module définit les routes pour :
- Demande de congés
- Validation des congés
- Consultation des soldes
- Gestion des types de congés

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.urls import path
from . import views

app_name = 'leave'

urlpatterns = [
    # Demandes de congés
    path('requests/', views.LeaveRequestListView.as_view(), name='leave_request_list'),
    path('requests/create/', views.LeaveRequestCreateView.as_view(), name='leave_request_create'),
    path('requests/<int:pk>/', views.LeaveRequestDetailView.as_view(), name='leave_request_detail'),
    path('requests/<int:pk>/edit/', views.LeaveRequestEditView.as_view(), name='leave_request_edit'),
    path('requests/<int:pk>/cancel/', views.LeaveRequestCancelView.as_view(), name='leave_request_cancel'),
    
    # Validation des congés
    path('approvals/', views.LeaveApprovalListView.as_view(), name='leave_approval_list'),
    path('approvals/<int:pk>/approve/', views.LeaveApprovalView.as_view(), name='leave_approve'),
    path('approvals/<int:pk>/reject/', views.LeaveRejectionView.as_view(), name='leave_reject'),
    
    # Soldes de congés
    path('balances/', views.LeaveBalanceListView.as_view(), name='leave_balance_list'),
    path('balances/<int:pk>/', views.LeaveBalanceDetailView.as_view(), name='leave_balance_detail'),
    
    # Types de congés
    path('types/', views.LeaveTypeListView.as_view(), name='leave_type_list'),
    path('types/<int:pk>/', views.LeaveTypeDetailView.as_view(), name='leave_type_detail'),
    
    # Jours fériés
    path('holidays/', views.HolidayListView.as_view(), name='holiday_list'),
    path('holidays/<int:pk>/', views.HolidayDetailView.as_view(), name='holiday_detail'),
    
    # Rapports
    path('reports/', views.LeaveReportView.as_view(), name='leave_report'),
    path('calendar/', views.LeaveCalendarView.as_view(), name='leave_calendar'),
]

