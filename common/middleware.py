"""
Middleware de gestion centralisée des erreurs pour PresencePro.

Ce middleware :
- Capture toutes les exceptions non gérées
- Applique une gestion d'erreurs cohérente
- Retourne des réponses d'erreur standardisées
- Log les erreurs avec contexte complet

Auteur: Système de Gestion de Présence
Date: 23 octobre 2025
"""

import logging
from django.http import JsonResponse, HttpResponseServerError
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from common.error_handler import error_handler, ErrorContext, ErrorCode, ErrorSeverity
from common.structured_logging import structured_logger


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware pour gestion centralisée des erreurs.
    
    Capture toutes les exceptions non gérées et applique
    une gestion d'erreurs cohérente à travers l'application.
    """
    
    def process_exception(self, request, exception):
        """
        Traite les exceptions non gérées.
        
        Args:
            request: Requête Django
            exception: Exception levée
            
        Returns:
            HttpResponse ou None
        """
        # Création du contexte d'erreur
        context = ErrorContext(
            user=getattr(request, 'user', None),
            request=request,
            operation=f"{request.method} {request.path}",
            additional_data={
                'view_name': getattr(request.resolver_match, 'view_name', None),
                'url_name': getattr(request.resolver_match, 'url_name', None),
                'args': getattr(request.resolver_match, 'args', []),
                'kwargs': getattr(request.resolver_match, 'kwargs', {})
            }
        )
        
        # Gestion centralisée de l'erreur
        code, message, severity = error_handler.handle_exception(exception, context)
        
        # Détermination du type de réponse selon la requête
        if self._is_ajax_request(request):
            return self._create_ajax_error_response(code, message, severity)
        elif self._is_api_request(request):
            return self._create_api_error_response(code, message, severity)
        else:
            return self._create_html_error_response(code, message, severity, request)
    
    def _is_ajax_request(self, request):
        """Vérifie si la requête est AJAX."""
        return request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    def _is_api_request(self, request):
        """Vérifie si la requête est une API."""
        return request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', '')
    
    def _create_ajax_error_response(self, code, message, severity):
        """Crée une réponse d'erreur pour AJAX."""
        return JsonResponse({
            'success': False,
            'error': {
                'code': code.value,
                'message': message,
                'severity': severity.value
            }
        }, status=self._get_http_status_for_severity(severity))
    
    def _create_api_error_response(self, code, message, severity):
        """Crée une réponse d'erreur pour API."""
        return JsonResponse({
            'success': False,
            'error': {
                'code': code.value,
                'message': message,
                'severity': severity.value,
                'timestamp': structured_logger._get_timestamp()
            }
        }, status=self._get_http_status_for_severity(severity))
    
    def _create_html_error_response(self, code, message, severity, request):
        """Crée une réponse d'erreur HTML."""
        # Template d'erreur selon la sévérité
        template_name = self._get_error_template(severity)
        
        context = {
            'error_code': code.value,
            'error_message': message,
            'error_severity': severity.value,
            'user': getattr(request, 'user', None),
            'debug': settings.DEBUG
        }
        
        try:
            html_content = render_to_string(template_name, context)
            return HttpResponseServerError(html_content)
        except Exception as template_error:
            # Fallback en cas d'erreur de template
            structured_logger.log_error(
                template_error,
                {'template_name': template_name, 'original_error_code': code.value},
                error_type="template_error"
            )
            
            return HttpResponseServerError(
                f"<h1>Erreur {code.value}</h1><p>{message}</p>"
            )
    
    def _get_error_template(self, severity):
        """Retourne le template d'erreur selon la sévérité."""
        template_mapping = {
            ErrorSeverity.LOW: 'errors/error_low.html',
            ErrorSeverity.MEDIUM: 'errors/error_medium.html',
            ErrorSeverity.HIGH: 'errors/error_high.html',
            ErrorSeverity.CRITICAL: 'errors/error_critical.html'
        }
        return template_mapping.get(severity, 'errors/error_medium.html')
    
    def _get_http_status_for_severity(self, severity):
        """Retourne le code HTTP selon la sévérité."""
        status_mapping = {
            ErrorSeverity.LOW: 400,      # Bad Request
            ErrorSeverity.MEDIUM: 422,   # Unprocessable Entity
            ErrorSeverity.HIGH: 500,     # Internal Server Error
            ErrorSeverity.CRITICAL: 503  # Service Unavailable
        }
        return status_mapping.get(severity, 500)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware pour logging des requêtes et réponses.
    
    Log toutes les requêtes importantes pour debugging
    et monitoring des performances.
    """
    
    def process_request(self, request):
        """Log la requête entrante."""
        # Log seulement les requêtes importantes
        if self._should_log_request(request):
            structured_logger.general_logger.info(
                "Requête entrante",
                method=request.method,
                path=request.path,
                user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                event_type="request_start"
            )
    
    def process_response(self, request, response):
        """Log la réponse sortante."""
        # Log seulement les réponses importantes
        if self._should_log_request(request):
            structured_logger.general_logger.info(
                "Requête terminée",
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                event_type="request_end"
            )
        
        return response
    
    def _should_log_request(self, request):
        """Détermine si la requête doit être loggée."""
        # Ne pas logger les requêtes statiques et de développement
        excluded_paths = [
            '/static/',
            '/media/',
            '/favicon.ico',
            '/admin/jsi18n/',
            '/__debug__/',
        ]
        
        return not any(request.path.startswith(path) for path in excluded_paths)
    
    def _get_client_ip(self, request):
        """Extrait l'IP réelle du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
