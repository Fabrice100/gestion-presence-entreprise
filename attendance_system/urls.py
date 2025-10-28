"""
Configuration des URLs pour le système de gestion de présence.

Ce fichier définit les routes principales de l'application :
- Administration Django
- Interface utilisateur (authentification, tableaux de bord)
- API REST (si nécessaire)

Auteur: Votre nom
Projet: Système de gestion de présence - Projet de fin de cycle
Version: 1.0
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Administration Django
    path('admin/', admin.site.urls),
    
    # Landing page
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
    
    # Test Frontend Complet
    path('test-ultra-simple/', TemplateView.as_view(template_name='test_ultra_simple.html'), name='test_ultra_simple'),
    
    # Interface utilisateur
    path('accounts/', include('accounts.urls')),
    path('attendance/', include('attendance.urls')),
    path('leave/', include('leave.urls')),
    path('reports/', include('reports.urls')),
    path('dashboard/', include('accounts.dashboard_urls')),
    
    # Interface RH
    path('hr/', include('accounts.hr_urls')),

]

# Configuration pour les fichiers statiques et médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
