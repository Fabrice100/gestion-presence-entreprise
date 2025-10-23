"""
Middleware d'optimisation des performances pour PresencePro.

Ce module fournit :
- Compression des réponses HTTP
- Optimisation des headers de cache
- Minification des ressources statiques
- Monitoring des performances
- Optimisation des sessions

Auteur: Système de Gestion de Présence
Date: 23 octobre 2025
"""

import gzip
import time
from typing import Optional
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.core.cache import cache
from common.structured_logging import structured_logger


class CompressionMiddleware(MiddlewareMixin):
    """
    Middleware de compression des réponses HTTP.
    
    Compresse automatiquement les réponses pour réduire
    la bande passante et améliorer les performances.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.min_length = 200  # Taille minimale pour compression
        self.compressible_types = [
            'text/html',
            'text/css',
            'text/javascript',
            'application/javascript',
            'application/json',
            'text/xml',
            'application/xml',
            'text/plain'
        ]
    
    def process_response(self, request, response):
        """
        Compresse la réponse si appropriée.
        
        Args:
            request: Requête Django
            response: Réponse Django
            
        Returns:
            Réponse compressée ou originale
        """
        # Vérification des conditions de compression
        if not self._should_compress(request, response):
            return response
        
        # Compression de la réponse
        try:
            compressed_content = gzip.compress(response.content)
            
            # Création de la nouvelle réponse
            compressed_response = HttpResponse(
                compressed_content,
                status=response.status_code,
                content_type=response.get('Content-Type', 'text/html')
            )
            
            # Copie des headers importants
            for header, value in response.items():
                if header.lower() not in ['content-length', 'content-encoding']:
                    compressed_response[header] = value
            
            # Ajout du header de compression
            compressed_response['Content-Encoding'] = 'gzip'
            compressed_response['Content-Length'] = str(len(compressed_content))
            
            # Logging de la compression
            compression_ratio = len(compressed_content) / len(response.content) * 100
            structured_logger.system_logger.debug(
                "Réponse compressée",
                original_size=len(response.content),
                compressed_size=len(compressed_content),
                compression_ratio=compression_ratio,
                path=request.path,
                event_type="response_compression"
            )
            
            return compressed_response
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'path': request.path, 'content_type': response.get('Content-Type')},
                error_type="compression_error"
            )
            return response
    
    def _should_compress(self, request, response) -> bool:
        """
        Détermine si la réponse doit être compressée.
        
        Args:
            request: Requête Django
            response: Réponse Django
            
        Returns:
            True si compression recommandée
        """
        # Vérification de la taille
        if len(response.content) < self.min_length:
            return False
        
        # Vérification du type de contenu
        content_type = response.get('Content-Type', '').split(';')[0]
        if content_type not in self.compressible_types:
            return False
        
        # Vérification du support client
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        if 'gzip' not in accept_encoding:
            return False
        
        # Vérification du header existant
        if response.get('Content-Encoding'):
            return False
        
        return True


class CacheHeadersMiddleware(MiddlewareMixin):
    """
    Middleware d'optimisation des headers de cache.
    
    Ajoute des headers de cache appropriés pour optimiser
    les performances côté client.
    """
    
    def process_response(self, request, response):
        """
        Ajoute des headers de cache appropriés.
        
        Args:
            request: Requête Django
            response: Réponse Django
            
        Returns:
            Réponse avec headers de cache
        """
        # Headers pour les ressources statiques
        if self._is_static_resource(request.path):
            response['Cache-Control'] = 'public, max-age=31536000'  # 1 an
            response['Expires'] = self._get_expires_header(31536000)
        
        # Headers pour les pages HTML
        elif self._is_html_response(response):
            if self._is_authenticated_user(request):
                # Utilisateurs authentifiés : cache court
                response['Cache-Control'] = 'private, max-age=300'  # 5 minutes
            else:
                # Utilisateurs anonymes : cache plus long
                response['Cache-Control'] = 'public, max-age=1800'  # 30 minutes
        
        # Headers pour les API
        elif self._is_api_response(request.path):
            response['Cache-Control'] = 'private, max-age=60'  # 1 minute
        
        # Headers de sécurité
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response
    
    def _is_static_resource(self, path: str) -> bool:
        """Vérifie si c'est une ressource statique."""
        static_paths = ['/static/', '/media/', '/favicon.ico']
        return any(path.startswith(sp) for sp in static_paths)
    
    def _is_html_response(self, response) -> bool:
        """Vérifie si c'est une réponse HTML."""
        content_type = response.get('Content-Type', '').split(';')[0]
        return content_type == 'text/html'
    
    def _is_authenticated_user(self, request) -> bool:
        """Vérifie si l'utilisateur est authentifié."""
        return hasattr(request, 'user') and request.user.is_authenticated
    
    def _is_api_response(self, path: str) -> bool:
        """Vérifie si c'est une réponse API."""
        return path.startswith('/api/')
    
    def _get_expires_header(self, max_age: int) -> str:
        """Génère un header Expires."""
        from datetime import datetime, timedelta
        expires_date = datetime.utcnow() + timedelta(seconds=max_age)
        return expires_date.strftime('%a, %d %b %Y %H:%M:%S GMT')


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware de monitoring des performances.
    
    Surveille les performances des requêtes et log
    les métriques importantes.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.slow_request_threshold = 2.0  # 2 secondes
        self.performance_log = []
    
    def process_request(self, request):
        """Enregistre le début de la requête."""
        request._start_time = time.time()
        request._initial_query_count = len(connection.queries) if hasattr(connection, 'queries') else 0
    
    def process_response(self, request, response):
        """
        Analyse les performances de la requête.
        
        Args:
            request: Requête Django
            response: Réponse Django
            
        Returns:
            Réponse originale
        """
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Métriques de base
            metrics = {
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'duration_ms': duration * 1000,
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                'ip_address': self._get_client_ip(request)
            }
            
            # Métriques de base de données
            if hasattr(connection, 'queries'):
                final_query_count = len(connection.queries)
                metrics['query_count'] = final_query_count - request._initial_query_count
                metrics['db_time_ms'] = sum(float(q['time']) for q in connection.queries[request._initial_query_count:]) * 1000
            
            # Logging des requêtes lentes
            if duration > self.slow_request_threshold:
                structured_logger.system_logger.warning(
                    "Requête lente détectée",
                    **metrics,
                    event_type="slow_request"
                )
            
            # Logging général des performances
            structured_logger.system_logger.info(
                "Performance de requête",
                **metrics,
                event_type="request_performance"
            )
            
            # Stockage des métriques pour analyse
            self.performance_log.append(metrics)
            
            # Limitation de la taille du log
            if len(self.performance_log) > 1000:
                self.performance_log = self.performance_log[-500:]
        
        return response
    
    def _get_client_ip(self, request):
        """Extrait l'IP réelle du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_performance_summary(self) -> dict:
        """
        Retourne un résumé des performances.
        
        Returns:
            Dictionnaire des métriques de performance
        """
        if not self.performance_log:
            return {'total_requests': 0}
        
        durations = [m['duration_ms'] for m in self.performance_log]
        query_counts = [m.get('query_count', 0) for m in self.performance_log]
        
        return {
            'total_requests': len(self.performance_log),
            'average_duration_ms': sum(durations) / len(durations),
            'max_duration_ms': max(durations),
            'min_duration_ms': min(durations),
            'average_query_count': sum(query_counts) / len(query_counts) if query_counts else 0,
            'slow_requests': len([d for d in durations if d > self.slow_request_threshold * 1000])
        }


class SessionOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware d'optimisation des sessions.
    
    Optimise la gestion des sessions pour améliorer
    les performances et réduire l'utilisation mémoire.
    """
    
    def process_request(self, request):
        """
        Optimise la session utilisateur.
        
        Args:
            request: Requête Django
        """
        if hasattr(request, 'session'):
            # Nettoyage périodique des sessions
            if not hasattr(request, '_session_cleaned'):
                self._cleanup_session(request)
                request._session_cleaned = True
    
    def _cleanup_session(self, request):
        """
        Nettoie la session des données inutiles.
        
        Args:
            request: Requête Django
        """
        session = request.session
        
        # Suppression des données temporaires anciennes
        keys_to_remove = []
        for key in session.keys():
            if key.startswith('temp_') and len(key) > 20:  # Clés temporaires longues
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del session[key]
        
        # Sauvegarde de la session si modifiée
        if keys_to_remove:
            session.save()
            structured_logger.system_logger.debug(
                "Session nettoyée",
                keys_removed=len(keys_to_remove),
                user_id=getattr(request.user, 'id', None),
                event_type="session_cleanup"
            )


# Import pour les métriques de DB
try:
    from django.db import connection
except ImportError:
    connection = None
