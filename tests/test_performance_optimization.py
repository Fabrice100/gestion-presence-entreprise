"""
Tests pour l'optimisation des performances.

Ce module teste :
- Cache intelligent avec stratégies multiples
- Optimisation des requêtes de base de données
- Pagination optimisée
- Middleware de compression et cache
- Monitoring des performances

Auteur: Système de Gestion de Présence
Date: 23 octobre 2025
"""

import time
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponse
from unittest.mock import patch, MagicMock
from datetime import date, timedelta

from common.intelligent_cache import (
    IntelligentCache, CacheStrategy, CacheMetrics,
    QuerySetCache, UserDataCache, PerformanceCache
)
from common.query_optimizer import (
    QueryOptimizer, PaginationOptimizer, DatabaseMonitor
)
from common.performance_middleware import (
    CompressionMiddleware, CacheHeadersMiddleware,
    PerformanceMonitoringMiddleware, SessionOptimizationMiddleware
)


class IntelligentCacheTestCase(TestCase):
    """Tests pour IntelligentCache."""
    
    def setUp(self):
        """Configuration des tests."""
        self.cache_service = IntelligentCache()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_cache_key_generation(self):
        """Test génération de clés de cache."""
        key1 = self.cache_service._generate_cache_key('test', 'arg1', 'arg2')
        key2 = self.cache_service._generate_cache_key('test', 'arg1', 'arg2')
        key3 = self.cache_service._generate_cache_key('test', 'arg2', 'arg1')
        
        self.assertEqual(key1, key2)  # Mêmes arguments = même clé
        self.assertNotEqual(key1, key3)  # Arguments différents = clés différentes
        self.assertTrue(key1.startswith('test:'))
    
    def test_cache_set_and_get(self):
        """Test stockage et récupération du cache."""
        key = 'test_key'
        value = {'data': 'test_value'}
        
        # Test stockage
        result = self.cache_service.set(key, value, strategy=CacheStrategy.DEFAULT)
        self.assertTrue(result)
        
        # Test récupération
        cached_value = self.cache_service.get(key, strategy=CacheStrategy.DEFAULT)
        self.assertEqual(cached_value, value)
        
        # Test métriques
        metrics = self.cache_service.get_metrics()
        self.assertEqual(metrics['hits'], 1)
        self.assertEqual(metrics['sets'], 1)
    
    def test_cache_miss(self):
        """Test cache miss."""
        key = 'non_existent_key'
        
        cached_value = self.cache_service.get(key)
        self.assertIsNone(cached_value)
        
        metrics = self.cache_service.get_metrics()
        self.assertEqual(metrics['misses'], 1)
    
    def test_get_or_set(self):
        """Test get_or_set avec fonction."""
        key = 'test_get_or_set'
        
        def expensive_function():
            return {'result': 'expensive_calculation'}
        
        # Premier appel - exécution de la fonction
        result1 = self.cache_service.get_or_set(key, expensive_function)
        self.assertEqual(result1['result'], 'expensive_calculation')
        
        # Deuxième appel - récupération depuis le cache
        result2 = self.cache_service.get_or_set(key, expensive_function)
        self.assertEqual(result2['result'], 'expensive_calculation')
        
        # Vérification que la fonction n'a été appelée qu'une fois
        metrics = self.cache_service.get_metrics()
        self.assertEqual(metrics['hits'], 1)
        self.assertEqual(metrics['sets'], 1)
    
    def test_cache_delete(self):
        """Test suppression du cache."""
        key = 'test_delete'
        value = 'test_value'
        
        # Stockage
        self.cache_service.set(key, value)
        
        # Vérification
        cached_value = self.cache_service.get(key)
        self.assertEqual(cached_value, value)
        
        # Suppression
        result = self.cache_service.delete(key)
        self.assertTrue(result)
        
        # Vérification de la suppression
        cached_value = self.cache_service.get(key)
        self.assertIsNone(cached_value)
    
    def test_cache_strategies(self):
        """Test différentes stratégies de cache."""
        key = 'strategy_test'
        value = 'test_value'
        
        # Test avec différentes stratégies
        strategies = [
            CacheStrategy.DEFAULT,
            CacheStrategy.FREQUENT_DATA,
            CacheStrategy.EXPENSIVE_CALCULATIONS
        ]
        
        for strategy in strategies:
            self.cache_service.set(key, value, strategy=strategy)
            cached_value = self.cache_service.get(key, strategy=strategy)
            self.assertEqual(cached_value, value)
    
    def test_metrics_reset(self):
        """Test remise à zéro des métriques."""
        # Génération de métriques
        self.cache_service.set('key1', 'value1')
        self.cache_service.get('key1')
        self.cache_service.get('key2')  # Miss
        
        metrics_before = self.cache_service.get_metrics()
        self.assertGreater(metrics_before['hits'], 0)
        self.assertGreater(metrics_before['misses'], 0)
        
        # Remise à zéro
        self.cache_service.reset_metrics()
        
        metrics_after = self.cache_service.get_metrics()
        self.assertEqual(metrics_after['hits'], 0)
        self.assertEqual(metrics_after['misses'], 0)


class UserDataCacheTestCase(TestCase):
    """Tests pour UserDataCache."""
    
    def setUp(self):
        """Configuration des tests."""
        self.cache_service = IntelligentCache()
        self.user_cache = UserDataCache(self.cache_service)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_profile_caching(self):
        """Test mise en cache du profil utilisateur."""
        profile_data = {
            'employee_id': 'EMP001',
            'department': 'IT',
            'position': 'Developer'
        }
        
        # Mise en cache
        result = self.user_cache.set_user_profile(self.user, profile_data)
        self.assertTrue(result)
        
        # Récupération
        cached_profile = self.user_cache.get_user_profile(self.user)
        self.assertEqual(cached_profile, profile_data)
    
    def test_user_cache_invalidation(self):
        """Test invalidation du cache utilisateur."""
        profile_data = {'test': 'data'}
        
        # Mise en cache
        self.user_cache.set_user_profile(self.user, profile_data)
        
        # Vérification
        cached_profile = self.user_cache.get_user_profile(self.user)
        self.assertEqual(cached_profile, profile_data)
        
        # Invalidation
        result = self.user_cache.invalidate_user_cache(self.user)
        self.assertTrue(result)
        
        # Vérification de l'invalidation
        cached_profile = self.user_cache.get_user_profile(self.user)
        self.assertIsNone(cached_profile)


class PerformanceCacheTestCase(TestCase):
    """Tests pour PerformanceCache."""
    
    def setUp(self):
        """Configuration des tests."""
        self.cache_service = IntelligentCache()
        self.performance_cache = PerformanceCache(self.cache_service)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_attendance_stats_caching(self):
        """Test mise en cache des statistiques de présence."""
        stats = {
            'total_days': 20,
            'total_hours': 160,
            'avg_hours_per_day': 8.0,
            'attendance_rate': 95.0
        }
        
        # Mise en cache
        result = self.performance_cache.set_attendance_stats(
            self.user, '2024-01-01', '2024-01-31', stats
        )
        self.assertTrue(result)
        
        # Récupération
        cached_stats = self.performance_cache.get_attendance_stats(
            self.user, '2024-01-01', '2024-01-31'
        )
        self.assertEqual(cached_stats, stats)
    
    def test_leave_balance_caching(self):
        """Test mise en cache du solde de congés."""
        balance = {
            'annual_leave': 25,
            'sick_leave': 10,
            'used_annual': 5,
            'used_sick': 2
        }
        
        # Mise en cache
        result = self.performance_cache.set_leave_balance(self.user, 2024, balance)
        self.assertTrue(result)
        
        # Récupération
        cached_balance = self.performance_cache.get_leave_balance(self.user, 2024)
        self.assertEqual(cached_balance, balance)


class QueryOptimizerTestCase(TestCase):
    """Tests pour QueryOptimizer."""
    
    def setUp(self):
        """Configuration des tests."""
        self.optimizer = QueryOptimizer()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('common.query_optimizer.structured_logger')
    def test_query_performance_logging(self, mock_logger):
        """Test logging des performances de requête."""
        self.optimizer.log_query_performance(
            'test_query', 1.5, 3, cache_hit=False
        )
        
        mock_logger.system_logger.info.assert_called_once()
        call_args = mock_logger.system_logger.info.call_args
        self.assertEqual(call_args[1]['query_name'], 'test_query')
        self.assertEqual(call_args[1]['duration_ms'], 1500)
        self.assertEqual(call_args[1]['query_count'], 3)
        self.assertFalse(call_args[1]['cache_hit'])


class PaginationOptimizerTestCase(TestCase):
    """Tests pour PaginationOptimizer."""
    
    def setUp(self):
        """Configuration des tests."""
        self.pagination_optimizer = PaginationOptimizer()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_pagination_metadata(self):
        """Test métadonnées de pagination."""
        # Mock d'un QuerySet
        mock_queryset = MagicMock()
        mock_queryset.__iter__ = MagicMock(return_value=iter(['item1', 'item2']))
        
        # Mock du Paginator
        with patch('common.query_optimizer.Paginator') as mock_paginator:
            mock_page = MagicMock()
            mock_page.object_list = ['item1', 'item2']
            mock_page.has_previous.return_value = False
            mock_page.has_next.return_value = True
            mock_page.next_page_number.return_value = 2
            
            mock_paginator_instance = MagicMock()
            mock_paginator_instance.page.return_value = mock_page
            mock_paginator_instance.num_pages = 5
            mock_paginator_instance.count = 100
            mock_paginator.return_value = mock_paginator_instance
            
            items, metadata = self.pagination_optimizer.paginate_queryset(
                mock_queryset, page=1, per_page=20
            )
            
            self.assertEqual(len(items), 2)
            self.assertEqual(metadata['current_page'], 1)
            self.assertEqual(metadata['total_pages'], 5)
            self.assertEqual(metadata['total_items'], 100)
            self.assertFalse(metadata['has_previous'])
            self.assertTrue(metadata['has_next'])
            self.assertEqual(metadata['next_page'], 2)


class CompressionMiddlewareTestCase(TestCase):
    """Tests pour CompressionMiddleware."""
    
    def setUp(self):
        """Configuration des tests."""
        self.factory = RequestFactory()
        self.middleware = CompressionMiddleware(lambda x: x)
    
    def test_should_compress_html(self):
        """Test compression d'une réponse HTML."""
        request = self.factory.get('/test/')
        request.META['HTTP_ACCEPT_ENCODING'] = 'gzip'
        
        response = HttpResponse('<html>Test content</html>', content_type='text/html')
        response['Content-Length'] = str(len(response.content))
        
        compressed_response = self.middleware.process_response(request, response)
        
        self.assertEqual(compressed_response['Content-Encoding'], 'gzip')
        self.assertLess(len(compressed_response.content), len(response.content))
    
    def test_should_not_compress_small_content(self):
        """Test non-compression de contenu trop petit."""
        request = self.factory.get('/test/')
        request.META['HTTP_ACCEPT_ENCODING'] = 'gzip'
        
        response = HttpResponse('OK', content_type='text/html')
        
        compressed_response = self.middleware.process_response(request, response)
        
        self.assertNotIn('Content-Encoding', compressed_response)
        self.assertEqual(compressed_response.content, response.content)
    
    def test_should_not_compress_without_gzip_support(self):
        """Test non-compression sans support gzip."""
        request = self.factory.get('/test/')
        # Pas de HTTP_ACCEPT_ENCODING
        
        response = HttpResponse('<html>Test content</html>', content_type='text/html')
        
        compressed_response = self.middleware.process_response(request, response)
        
        self.assertNotIn('Content-Encoding', compressed_response)
        self.assertEqual(compressed_response.content, response.content)


class CacheHeadersMiddlewareTestCase(TestCase):
    """Tests pour CacheHeadersMiddleware."""
    
    def setUp(self):
        """Configuration des tests."""
        self.factory = RequestFactory()
        self.middleware = CacheHeadersMiddleware(lambda x: x)
    
    def test_static_resource_headers(self):
        """Test headers pour ressources statiques."""
        request = self.factory.get('/static/css/style.css')
        response = HttpResponse('body { color: red; }', content_type='text/css')
        
        processed_response = self.middleware.process_response(request, response)
        
        self.assertIn('Cache-Control', processed_response)
        self.assertIn('max-age=31536000', processed_response['Cache-Control'])
        self.assertIn('Expires', processed_response)
    
    def test_html_response_headers(self):
        """Test headers pour réponses HTML."""
        request = self.factory.get('/test/')
        response = HttpResponse('<html>Test</html>', content_type='text/html')
        
        processed_response = self.middleware.process_response(request, response)
        
        self.assertIn('Cache-Control', processed_response)
        self.assertIn('X-Content-Type-Options', processed_response)
        self.assertEqual(processed_response['X-Content-Type-Options'], 'nosniff')
    
    def test_security_headers(self):
        """Test headers de sécurité."""
        request = self.factory.get('/test/')
        response = HttpResponse('<html>Test</html>', content_type='text/html')
        
        processed_response = self.middleware.process_response(request, response)
        
        self.assertEqual(processed_response['X-Frame-Options'], 'DENY')
        self.assertEqual(processed_response['X-XSS-Protection'], '1; mode=block')


class PerformanceMonitoringMiddlewareTestCase(TestCase):
    """Tests pour PerformanceMonitoringMiddleware."""
    
    def setUp(self):
        """Configuration des tests."""
        self.factory = RequestFactory()
        self.middleware = PerformanceMonitoringMiddleware(lambda x: x)
    
    def test_performance_monitoring(self):
        """Test monitoring des performances."""
        request = self.factory.get('/test/')
        response = HttpResponse('<html>Test</html>', content_type='text/html')
        
        # Process request
        self.middleware.process_request(request)
        
        # Simuler une requête lente
        time.sleep(0.1)
        
        # Process response
        processed_response = self.middleware.process_response(request, response)
        
        # Vérifier que les métriques sont enregistrées
        summary = self.middleware.get_performance_summary()
        self.assertEqual(summary['total_requests'], 1)
        self.assertGreater(summary['average_duration_ms'], 0)
    
    def test_performance_summary(self):
        """Test résumé des performances."""
        # Simuler plusieurs requêtes
        for i in range(5):
            request = self.factory.get(f'/test{i}/')
            response = HttpResponse('<html>Test</html>')
            
            self.middleware.process_request(request)
            time.sleep(0.01)  # Simuler une petite latence
            self.middleware.process_response(request, response)
        
        summary = self.middleware.get_performance_summary()
        
        self.assertEqual(summary['total_requests'], 5)
        self.assertGreater(summary['average_duration_ms'], 0)
        self.assertGreater(summary['max_duration_ms'], summary['min_duration_ms'])


class PerformanceIntegrationTestCase(TestCase):
    """Tests d'intégration pour l'optimisation des performances."""
    
    def setUp(self):
        """Configuration des tests."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_cache_and_query_optimization_integration(self):
        """Test intégration cache et optimisation des requêtes."""
        cache_service = IntelligentCache()
        optimizer = QueryOptimizer()
        
        # Test avec cache
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        # Premier appel - pas de cache
        with patch.object(optimizer, 'get_user_attendances_optimized') as mock_method:
            mock_method.return_value = []
            
            result1 = optimizer.get_user_attendances_optimized(
                self.user, start_date, end_date
            )
            
            # Deuxième appel - avec cache
            result2 = optimizer.get_user_attendances_optimized(
                self.user, start_date, end_date
            )
            
            # La méthode ne devrait être appelée qu'une fois
            self.assertEqual(mock_method.call_count, 1)
    
    def test_performance_metrics_accuracy(self):
        """Test précision des métriques de performance."""
        cache_service = IntelligentCache()
        
        # Génération de métriques connues
        cache_service.set('key1', 'value1')
        cache_service.set('key2', 'value2')
        cache_service.get('key1')  # Hit
        cache_service.get('key2')  # Hit
        cache_service.get('key3')  # Miss
        
        metrics = cache_service.get_metrics()
        
        self.assertEqual(metrics['hits'], 2)
        self.assertEqual(metrics['misses'], 1)
        self.assertEqual(metrics['sets'], 2)
        self.assertEqual(metrics['hit_rate'], 66.67)  # 2/3 * 100
