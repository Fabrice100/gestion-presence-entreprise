"""
Vues pour le système de notifications.

Ce module contient les vues pour :
- Affichage des notifications
- Gestion des paramètres
- API pour les notifications temps réel

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, UpdateView
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy
import json

from .models import Notification, NotificationSettings
from .services import NotificationService


class NotificationListView(LoginRequiredMixin, ListView):
    """
    Liste des notifications pour l'utilisateur connecté.
    """
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques des notifications
        context['unread_count'] = NotificationService.get_unread_count(self.request.user)
        context['total_count'] = Notification.objects.filter(user=self.request.user).count()
        
        # Répartition par type
        notifications = Notification.objects.filter(user=self.request.user)
        context['type_stats'] = {
            'info': notifications.filter(notification_type='info').count(),
            'success': notifications.filter(notification_type='success').count(),
            'warning': notifications.filter(notification_type='warning').count(),
            'error': notifications.filter(notification_type='error').count(),
        }
        
        return context


@method_decorator(csrf_exempt, name='dispatch')
class NotificationSettingsView(LoginRequiredMixin, UpdateView):
    """
    Gestion des paramètres de notifications.
    """
    model = NotificationSettings
    template_name = 'notifications/notification_settings.html'
    fields = [
        'email_enabled', 'in_app_enabled', 'frequency',
        'notify_leave_requests', 'notify_attendance_anomalies', 'notify_system_updates',
        'silent_hours_start', 'silent_hours_end'
    ]
    success_url = reverse_lazy('notifications:settings')
    
    def get_object(self):
        obj, created = NotificationSettings.objects.get_or_create(
            user=self.request.user
        )
        return obj
    
    def form_valid(self, form):
        messages.success(self.request, 'Paramètres de notifications mis à jour avec succès.')
        return super().form_valid(form)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """
    Marque une notification comme lue.
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    
    notification.mark_as_read()
    
    return JsonResponse({
        'success': True,
        'unread_count': NotificationService.get_unread_count(request.user)
    })


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """
    Marque toutes les notifications comme lues.
    """
    NotificationService.mark_all_as_read(request.user)
    
    return JsonResponse({
        'success': True,
        'unread_count': 0
    })


@login_required
def get_notifications_api(request):
    """
    API pour récupérer les notifications (AJAX).
    """
    # Paramètres de la requête
    limit = int(request.GET.get('limit', 10))
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
    
    # Construire la requête
    queryset = Notification.objects.filter(user=request.user)
    
    if unread_only:
        queryset = queryset.filter(is_read=False)
    
    notifications = queryset.order_by('-created_at')[:limit]
    
    # Formater les données
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'priority': notification.priority,
            'is_read': notification.is_read,
            'link': notification.action_url,
            'created_at': notification.created_at.isoformat(),
        })
    
    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': NotificationService.get_unread_count(request.user)
    })


@login_required
def notification_badge_api(request):
    """
    API pour récupérer le badge de notifications (nombre non lues).
    """
    unread_count = NotificationService.get_unread_count(request.user)
    
    return JsonResponse({
        'unread_count': unread_count,
        'has_notifications': unread_count > 0
    })


@login_required
def test_notification(request):
    """
    Crée une notification de test pour l'utilisateur connecté.
    """
    notification = NotificationService.create_notification(
        user=request.user,
        title="Notification de test",
        message="Ceci est une notification de test pour vérifier le fonctionnement du système.",
        notification_type='info',
        action_url='/dashboard/'
    )
    
    messages.success(request, 'Notification de test créée avec succès.')
    return JsonResponse({'success': True, 'notification_id': notification.id})
