"""
URLs pour l'application notifications.

Ce module définit les routes pour :
- Liste des notifications
- Paramètres de notifications
- API pour notifications temps réel

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Interface utilisateur
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('settings/', views.NotificationSettingsView.as_view(), name='settings'),
    
    # API pour notifications temps réel
    path('api/notifications/', views.get_notifications_api, name='api_notifications'),
    path('api/badge/', views.notification_badge_api, name='api_badge'),
    path('api/mark-read/<int:notification_id>/', views.mark_notification_read, name='api_mark_read'),
    path('api/mark-all-read/', views.mark_all_notifications_read, name='api_mark_all_read'),
    
    # Test et debug
    path('test/', views.test_notification, name='test_notification'),
]
