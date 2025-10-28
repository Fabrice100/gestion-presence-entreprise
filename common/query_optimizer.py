"""
Service d'optimisation des requêtes de base de données pour PresencePro.

Ce module fournit :
- Optimisation automatique des requêtes avec select_related/prefetch_related
- Pagination intelligente des listes
- Requêtes optimisées pour les statistiques
- Monitoring des performances des requêtes
- Cache des requêtes fréquentes

Auteur: Système de Gestion de Présence
Date: 23 octobre 2025
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from django.db import connection
from django.db.models import QuerySet, Prefetch, Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from common.structured_logging import structured_logger
from common.intelligent_cache import intelligent_cache, CacheStrategy


class QueryOptimizer:
    """
    Optimiseur de requêtes de base de données.
    
    Fournit des méthodes optimisées pour les requêtes fréquentes
    avec monitoring des performances.
    """
    
    def __init__(self):
        self.cache = intelligent_cache
    
    def log_query_performance(self, query_name: str, duration: float, 
                            query_count: int, cache_hit: bool = False):
        """
        Log les performances d'une requête.
        
        Args:
            query_name: Nom de la requête
            duration: Durée en secondes
            query_count: Nombre de requêtes DB
            cache_hit: True si résultat depuis le cache
        """
        structured_logger.system_logger.info(
            "Performance de requête",
            query_name=query_name,
            duration_ms=duration * 1000,
            query_count=query_count,
            cache_hit=cache_hit,
            event_type="query_performance"
        )
    
    def get_user_attendances_optimized(self, user: User, start_date: date, 
                                    end_date: date) -> QuerySet:
        """
        Récupère les présences d'un utilisateur avec optimisations.
        
        Args:
            user: Utilisateur Django
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            QuerySet optimisé des présences
        """
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        # Clé de cache pour cette requête
        cache_key = self.cache._generate_cache_key(
            'user_attendances', user.id, start_date, end_date
        )
        
        # Tentative de récupération depuis le cache
        cached_result = self.cache.get(cache_key, CacheStrategy.FREQUENT_DATA)
        if cached_result is not None:
            self.log_query_performance(
                'get_user_attendances_optimized', 
                time.time() - start_time, 
                0, 
                cache_hit=True
            )
            return cached_result
        
        # Requête optimisée avec select_related et prefetch_related
        queryset = user.attendances.filter(
            date__range=[start_date, end_date]
        ).select_related(
            'employee'
        ).prefetch_related(
            Prefetch(
                'attendanceanomaly_set',
                queryset=user.attendances.model.attendanceanomaly_set.related.related_model.objects.all()
            )
        ).order_by('-date', '-time')
        
        # Mise en cache du résultat
        self.cache.set(cache_key, queryset, 1800, CacheStrategy.FREQUENT_DATA)
        
        final_queries = len(connection.queries)
        self.log_query_performance(
            'get_user_attendances_optimized',
            time.time() - start_time,
            final_queries - initial_queries
        )
        
        return queryset
    
    def get_department_employees_optimized(self, department_id: int) -> QuerySet:
        """
        Récupère les employés d'un département avec optimisations.
        
        Args:
            department_id: ID du département
            
        Returns:
            QuerySet optimisé des employés
        """
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        cache_key = self.cache._generate_cache_key('department_employees', department_id)
        
        cached_result = self.cache.get(cache_key, CacheStrategy.FREQUENT_DATA)
        if cached_result is not None:
            self.log_query_performance(
                'get_department_employees_optimized',
                time.time() - start_time,
                0,
                cache_hit=True
            )
            return cached_result
        
        # Requête optimisée
        queryset = User.objects.filter(
            employee_profile__department_id=department_id,
            employee_profile__is_active=True
        ).select_related(
            'employee_profile__department'
        ).prefetch_related(
            'employee_profile__leavebalance_set'
        ).order_by('employee_profile__employee_id')
        
        self.cache.set(cache_key, queryset, 3600, CacheStrategy.FREQUENT_DATA)
        
        final_queries = len(connection.queries)
        self.log_query_performance(
            'get_department_employees_optimized',
            time.time() - start_time,
            final_queries - initial_queries
        )
        
        return queryset
    
    def get_attendance_statistics_optimized(self, user: User, year: int) -> Dict[str, Any]:
        """
        Calcule les statistiques de présence avec optimisations.
        
        Args:
            user: Utilisateur Django
            year: Année
            
        Returns:
            Dictionnaire des statistiques
        """
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        cache_key = self.cache._generate_cache_key('attendance_stats', user.id, year)
        
        cached_result = self.cache.get(cache_key, CacheStrategy.EXPENSIVE_CALCULATIONS)
        if cached_result is not None:
            self.log_query_performance(
                'get_attendance_statistics_optimized',
                time.time() - start_time,
                0,
                cache_hit=True
            )
            return cached_result
        
        # Calculs optimisés avec une seule requête
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        stats = user.attendances.filter(
            date__range=[start_date, end_date]
        ).aggregate(
            total_days=Count('id'),
            total_hours=Sum('worked_hours'),
            avg_hours_per_day=Avg('worked_hours'),
            late_arrivals=Count('id', filter=Q(status='late')),
            early_departures=Count('id', filter=Q(status='early')),
            anomalies=Count('attendanceanomaly')
        )
        
        # Calculs supplémentaires
        stats['attendance_rate'] = (stats['total_days'] / 365) * 100 if stats['total_days'] else 0
        stats['year'] = year
        
        # Mise en cache
        self.cache.set(cache_key, stats, 3600, CacheStrategy.EXPENSIVE_CALCULATIONS)
        
        final_queries = len(connection.queries)
        self.log_query_performance(
            'get_attendance_statistics_optimized',
            time.time() - start_time,
            final_queries - initial_queries
        )
        
        return stats
    
    def get_leave_requests_optimized(self, user: User, status: Optional[str] = None) -> QuerySet:
        """
        Récupère les demandes de congés avec optimisations.
        
        Args:
            user: Utilisateur Django
            status: Statut des demandes (optionnel)
            
        Returns:
            QuerySet optimisé des demandes de congés
        """
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        cache_key = self.cache._generate_cache_key('leave_requests', user.id, status)
        
        cached_result = self.cache.get(cache_key, CacheStrategy.FREQUENT_DATA)
        if cached_result is not None:
            self.log_query_performance(
                'get_leave_requests_optimized',
                time.time() - start_time,
                0,
                cache_hit=True
            )
            return cached_result
        
        # Requête optimisée
        queryset = user.leave_requests.all()
        
        if status:
            queryset = queryset.filter(status=status)
        
        queryset = queryset.select_related(
            'leave_type',
            'manager',
            'rh_approver'
        ).prefetch_related(
            'leavebalance_set'
        ).order_by('-created_at')
        
        self.cache.set(cache_key, queryset, 1800, CacheStrategy.FREQUENT_DATA)
        
        final_queries = len(connection.queries)
        self.log_query_performance(
            'get_leave_requests_optimized',
            time.time() - start_time,
            final_queries - initial_queries
        )
        
        return queryset


class PaginationOptimizer:
    """Optimiseur de pagination pour les listes."""
    
    def __init__(self):
        self.cache = intelligent_cache
    
    def paginate_queryset(self, queryset: QuerySet, page: int, per_page: int = 20,
                         cache_key: Optional[str] = None) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Pagine un QuerySet avec optimisations.
        
        Args:
            queryset: QuerySet à paginer
            page: Numéro de page
            per_page: Nombre d'éléments par page
            cache_key: Clé de cache (optionnel)
            
        Returns:
            Tuple (éléments de la page, métadonnées de pagination)
        """
        start_time = time.time()
        
        # Tentative de récupération depuis le cache
        if cache_key:
            cached_result = self.cache.get(cache_key, CacheStrategy.FREQUENT_DATA)
            if cached_result is not None:
                return cached_result
        
        # Pagination optimisée
        paginator = Paginator(queryset, per_page)
        
        try:
            page_obj = paginator.page(page)
            items = list(page_obj.object_list)
            
            pagination_data = {
                'items': items,
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
                'per_page': per_page
            }
            
            # Mise en cache
            if cache_key:
                self.cache.set(cache_key, pagination_data, 900, CacheStrategy.FREQUENT_DATA)
            
            structured_logger.system_logger.debug(
                "Pagination optimisée",
                page=page,
                per_page=per_page,
                total_items=paginator.count,
                duration_ms=(time.time() - start_time) * 1000,
                event_type="pagination_performance"
            )
            
            return items, pagination_data
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'page': page, 'per_page': per_page, 'cache_key': cache_key},
                error_type="pagination_error"
            )
            return [], {}
    
    def get_attendance_list_paginated(self, user: User, page: int = 1, 
                                    per_page: int = 20) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Pagine la liste des présences d'un utilisateur.
        
        Args:
            user: Utilisateur Django
            page: Numéro de page
            per_page: Nombre d'éléments par page
            
        Returns:
            Tuple (présences de la page, métadonnées)
        """
        cache_key = self.cache._generate_cache_key(
            'attendance_list_paginated', user.id, page, per_page
        )
        
        queryset = user.attendances.select_related('employee').order_by('-date', '-time')
        
        return self.paginate_queryset(queryset, page, per_page, cache_key)
    
    def get_leave_requests_list_paginated(self, user: User, page: int = 1,
                                        per_page: int = 20) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Pagine la liste des demandes de congés d'un utilisateur.
        
        Args:
            user: Utilisateur Django
            page: Numéro de page
            per_page: Nombre d'éléments par page
            
        Returns:
            Tuple (demandes de la page, métadonnées)
        """
        cache_key = self.cache._generate_cache_key(
            'leave_requests_list_paginated', user.id, page, per_page
        )
        
        queryset = user.leave_requests.select_related(
            'leave_type', 'manager', 'rh_approver'
        ).order_by('-created_at')
        
        return self.paginate_queryset(queryset, page, per_page, cache_key)


class DatabaseMonitor:
    """Moniteur des performances de base de données."""
    
    def __init__(self):
        self.query_log = []
        self.slow_query_threshold = 1.0  # 1 seconde
    
    def log_slow_query(self, query: str, duration: float, params: Dict[str, Any]):
        """
        Log une requête lente.
        
        Args:
            query: Requête SQL
            duration: Durée en secondes
            params: Paramètres de la requête
        """
        if duration > self.slow_query_threshold:
            structured_logger.system_logger.warning(
                "Requête lente détectée",
                query=query[:200],  # Limite la longueur
                duration_ms=duration * 1000,
                params=params,
                event_type="slow_query"
            )
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """
        Retourne les statistiques des requêtes.
        
        Returns:
            Dictionnaire des statistiques
        """
        if not connection.queries:
            return {'total_queries': 0, 'total_time': 0}
        
        total_time = sum(float(query['time']) for query in connection.queries)
        
        return {
            'total_queries': len(connection.queries),
            'total_time': total_time,
            'average_time': total_time / len(connection.queries),
            'slow_queries': len([q for q in connection.queries if float(q['time']) > self.slow_query_threshold])
        }
    
    def reset_query_log(self):
        """Remet à zéro le log des requêtes."""
        connection.queries_log.clear()


# Instances globales des optimiseurs
query_optimizer = QueryOptimizer()
pagination_optimizer = PaginationOptimizer()
database_monitor = DatabaseMonitor()


