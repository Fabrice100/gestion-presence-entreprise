"""
Tests pour la gestion centralisée des erreurs.

Ce module teste :
- Gestion des exceptions Django
- Gestion des erreurs personnalisées
- Création de réponses d'erreur standardisées
- Middleware de gestion d'erreurs
- Logging structuré des erreurs

Auteur: Système de Gestion de Présence
Date: 23 octobre 2025
"""

from django.test import TestCase, RequestFactory
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404
from django.db import DatabaseError
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from common.error_handler import (
    ErrorHandler, ErrorCode, ErrorSeverity, ErrorContext, 
    SystemError, error_handler, handle_errors
)
from common.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from common.structured_logging import structured_logger


class ErrorHandlerTestCase(TestCase):
    """Tests pour ErrorHandler."""
    
    def setUp(self):
        """Configuration des tests."""
        self.handler = ErrorHandler()
        self.factory = RequestFactory()
    
    def test_handle_validation_error(self):
        """Test gestion des erreurs de validation."""
        exception = ValidationError("Données invalides")
        context = ErrorContext(operation="test_validation")
        
        code, message, severity = self.handler.handle_exception(exception, context)
        
        self.assertEqual(code, ErrorCode.VALIDATION_ERROR)
        self.assertIn("invalides", message)
        self.assertEqual(severity, ErrorSeverity.MEDIUM)
    
    def test_handle_permission_error(self):
        """Test gestion des erreurs de permission."""
        exception = PermissionDenied("Accès refusé")
        context = ErrorContext(operation="test_permission")
        
        code, message, severity = self.handler.handle_exception(exception, context)
        
        self.assertEqual(code, ErrorCode.PERMISSION_DENIED)
        self.assertIn("autorisation", message)
        self.assertEqual(severity, ErrorSeverity.HIGH)
    
    def test_handle_not_found_error(self):
        """Test gestion des erreurs 404."""
        exception = Http404("Ressource non trouvée")
        context = ErrorContext(operation="test_not_found")
        
        code, message, severity = self.handler.handle_exception(exception, context)
        
        self.assertEqual(code, ErrorCode.NOT_FOUND)
        self.assertIn("trouvée", message)
        self.assertEqual(severity, ErrorSeverity.MEDIUM)
    
    def test_handle_database_error(self):
        """Test gestion des erreurs de base de données."""
        exception = DatabaseError("Erreur DB")
        context = ErrorContext(operation="test_database")
        
        code, message, severity = self.handler.handle_exception(exception, context)
        
        self.assertEqual(code, ErrorCode.DATABASE_ERROR)
        self.assertIn("base de données", message)
        self.assertEqual(severity, ErrorSeverity.HIGH)
    
    def test_handle_system_error(self):
        """Test gestion des erreurs système personnalisées."""
        context = ErrorContext(operation="test_system")
        exception = SystemError(
            code=ErrorCode.PUNCH_GPS_INVALID,
            message="GPS invalide",
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        
        code, message, severity = self.handler.handle_exception(exception, context)
        
        self.assertEqual(code, ErrorCode.PUNCH_GPS_INVALID)
        self.assertEqual(message, "GPS invalide")
        self.assertEqual(severity, ErrorSeverity.MEDIUM)
    
    def test_handle_generic_error(self):
        """Test gestion des erreurs génériques."""
        exception = ValueError("Erreur générique")
        context = ErrorContext(operation="test_generic")
        
        code, message, severity = self.handler.handle_exception(exception, context)
        
        self.assertEqual(code, ErrorCode.UNKNOWN_ERROR)
        self.assertIn("inattendue", message)
        self.assertEqual(severity, ErrorSeverity.HIGH)
    
    def test_create_error_response(self):
        """Test création de réponse d'erreur standardisée."""
        response = self.handler.create_error_response(
            ErrorCode.VALIDATION_ERROR,
            "Message d'erreur",
            ErrorSeverity.MEDIUM,
            {'field': 'test'}
        )
        
        self.assertFalse(response['success'])
        self.assertEqual(response['error']['code'], 'VALIDATION_ERROR')
        self.assertEqual(response['error']['message'], 'Message d\'erreur')
        self.assertEqual(response['error']['severity'], 'MEDIUM')
        self.assertEqual(response['error']['details']['field'], 'test')


class ErrorContextTestCase(TestCase):
    """Tests pour ErrorContext."""
    
    def setUp(self):
        """Configuration des tests."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_error_context_with_request(self):
        """Test création de contexte avec requête."""
        request = self.factory.get('/test/')
        request.user = self.user
        
        context = ErrorContext(
            user=self.user,
            request=request,
            operation='test_operation',
            additional_data={'key': 'value'}
        )
        
        context_dict = context.to_dict()
        
        self.assertEqual(context_dict['user_id'], self.user.id)
        self.assertEqual(context_dict['operation'], 'test_operation')
        self.assertEqual(context_dict['additional_data']['key'], 'value')
        self.assertIsNotNone(context_dict['ip_address'])
        self.assertIsNotNone(context_dict['path'])
    
    def test_error_context_without_request(self):
        """Test création de contexte sans requête."""
        context = ErrorContext(
            user=self.user,
            operation='test_operation'
        )
        
        context_dict = context.to_dict()
        
        self.assertEqual(context_dict['user_id'], self.user.id)
        self.assertEqual(context_dict['operation'], 'test_operation')
        self.assertIsNone(context_dict.get('ip_address'))
        self.assertIsNone(context_dict.get('path'))


class SystemErrorTestCase(TestCase):
    """Tests pour SystemError."""
    
    def test_system_error_creation(self):
        """Test création d'erreur système."""
        context = ErrorContext(operation='test')
        exception = ValueError("Original error")
        
        system_error = SystemError(
            code=ErrorCode.PUNCH_GPS_INVALID,
            message="GPS invalide",
            severity=ErrorSeverity.MEDIUM,
            context=context,
            original_exception=exception
        )
        
        self.assertEqual(system_error.code, ErrorCode.PUNCH_GPS_INVALID)
        self.assertEqual(system_error.message, "GPS invalide")
        self.assertEqual(system_error.severity, ErrorSeverity.MEDIUM)
        self.assertEqual(system_error.context, context)
        self.assertEqual(system_error.original_exception, exception)


class ErrorHandlingMiddlewareTestCase(TestCase):
    """Tests pour ErrorHandlingMiddleware."""
    
    def setUp(self):
        """Configuration des tests."""
        self.factory = RequestFactory()
        self.middleware = ErrorHandlingMiddleware(lambda x: x)  # Mock get_response
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_is_ajax_request(self):
        """Test détection requête AJAX."""
        request = self.factory.get('/test/')
        request.headers = {'X-Requested-With': 'XMLHttpRequest'}
        
        self.assertTrue(self.middleware._is_ajax_request(request))
    
    def test_is_api_request(self):
        """Test détection requête API."""
        request = self.factory.get('/api/test/')
        request.headers = {'Accept': 'application/json'}
        
        self.assertTrue(self.middleware._is_api_request(request))
    
    def test_get_http_status_for_severity(self):
        """Test mapping sévérité -> code HTTP."""
        self.assertEqual(
            self.middleware._get_http_status_for_severity(ErrorSeverity.LOW), 400
        )
        self.assertEqual(
            self.middleware._get_http_status_for_severity(ErrorSeverity.MEDIUM), 422
        )
        self.assertEqual(
            self.middleware._get_http_status_for_severity(ErrorSeverity.HIGH), 500
        )
        self.assertEqual(
            self.middleware._get_http_status_for_severity(ErrorSeverity.CRITICAL), 503
        )
    
    @patch('common.middleware.render_to_string')
    def test_process_exception_html(self, mock_render):
        """Test traitement d'exception pour HTML."""
        mock_render.return_value = "<html>Error</html>"
        
        request = self.factory.get('/test/')
        request.user = self.user
        request.resolver_match = MagicMock()
        request.resolver_match.view_name = 'test_view'
        request.resolver_match.url_name = 'test_url'
        request.resolver_match.args = []
        request.resolver_match.kwargs = {}
        
        exception = ValidationError("Test error")
        
        response = self.middleware.process_exception(request, exception)
        
        self.assertIsNotNone(response)
        # La réponse HTML utilise HttpResponseServerError (500)
        self.assertEqual(response.status_code, 500)
    
    def test_process_exception_ajax(self):
        """Test traitement d'exception pour AJAX."""
        request = self.factory.get('/test/')
        request.user = self.user
        request.headers = {'X-Requested-With': 'XMLHttpRequest'}
        request.resolver_match = MagicMock()
        request.resolver_match.view_name = 'test_view'
        request.resolver_match.url_name = 'test_url'
        request.resolver_match.args = []
        request.resolver_match.kwargs = {}
        
        exception = ValidationError("Test error")
        
        response = self.middleware.process_exception(request, exception)
        
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 422)
        self.assertIn('application/json', response['Content-Type'])


class RequestLoggingMiddlewareTestCase(TestCase):
    """Tests pour RequestLoggingMiddleware."""
    
    def setUp(self):
        """Configuration des tests."""
        self.factory = RequestFactory()
        self.middleware = RequestLoggingMiddleware(lambda x: x)  # Mock get_response
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_should_log_request(self):
        """Test détermination si requête doit être loggée."""
        request = self.factory.get('/test/')
        self.assertTrue(self.middleware._should_log_request(request))
        
        request = self.factory.get('/static/css/style.css')
        self.assertFalse(self.middleware._should_log_request(request))
        
        request = self.factory.get('/media/uploads/file.pdf')
        self.assertFalse(self.middleware._should_log_request(request))
    
    def test_get_client_ip(self):
        """Test extraction IP client."""
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        
        ip = self.middleware._get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
        
        # Test avec X-Forwarded-For
        request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 192.168.1.1'
        ip = self.middleware._get_client_ip(request)
        self.assertEqual(ip, '203.0.113.1')


class ErrorHandlingIntegrationTestCase(TestCase):
    """Tests d'intégration pour la gestion d'erreurs."""
    
    def setUp(self):
        """Configuration des tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('common.error_handler.structured_logger')
    def test_error_logging_integration(self, mock_logger):
        """Test intégration avec le logging structuré."""
        original_logger = error_handler.logger
        error_handler.logger = mock_logger
        self.addCleanup(lambda: setattr(error_handler, 'logger', original_logger))
        
        exception = ValidationError("Test error")
        context = ErrorContext(
            user=self.user,
            operation='test_operation'
        )
        
        error_handler.handle_exception(exception, context)
        
        # Vérification que le logger a été appelé
        mock_logger.log_error.assert_called_once()
    
    def test_error_codes_completeness(self):
        """Test que tous les codes d'erreur ont des messages."""
        handler = ErrorHandler()
        
        for error_code in ErrorCode:
            self.assertIn(error_code, handler.error_messages)
            self.assertIsNotNone(handler.error_messages[error_code])
            self.assertGreater(len(handler.error_messages[error_code]), 0)
    
    def test_error_severity_mapping(self):
        """Test mapping des sévérités."""
        severity_mapping = {
            ErrorSeverity.LOW: 400,
            ErrorSeverity.MEDIUM: 422,
            ErrorSeverity.HIGH: 500,
            ErrorSeverity.CRITICAL: 503
        }
        
        middleware = ErrorHandlingMiddleware(lambda x: x)
        
        for severity, expected_status in severity_mapping.items():
            actual_status = middleware._get_http_status_for_severity(severity)
            self.assertEqual(actual_status, expected_status)
