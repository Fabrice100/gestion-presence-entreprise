"""
Service de cache intelligent pour PresencePro.

Ce module fournit :
- Cache multi-niveaux avec stratégies adaptatives
- Cache des requêtes fréquentes et calculs coûteux
- Invalidation intelligente du cache
- Métriques de performance du cache
- Cache distribué pour production

Auteur: Système de Gestion de Présence
Date: 23 octobre 2025
"""

import hashlib
import json
import time
from typing import Any, Optional, Dict, List, Callable
from django.core.cache import cache, caches
from django.conf import settings
from django.db.models import QuerySet
from django.contrib.auth.models import User
from common.structured_logging import structured_logger


class CacheStrategy:
    """Stratégies de cache disponibles."""
    
    FREQUENT_DATA = 'frequent_data'
    EXPENSIVE_CALCULATIONS = 'expensive_calculations'
    SESSIONS = 'sessions'
    DEFAULT = 'default'


class CacheMetrics:
    """Métriques de performance du cache."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.total_time = 0.0
    
    def hit_rate(self) -> float:
        """Calcule le taux de réussite du cache."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit les métriques en dictionnaire."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'sets': self.sets,
            'deletes': self.deletes,
            'hit_rate': self.hit_rate(),
            'total_time': self.total_time
        }


class IntelligentCache:
    """
    Service de cache intelligent avec stratégies adaptatives.
    
    Fournit un cache multi-niveaux avec invalidation intelligente
    et métriques de performance pour optimiser les performances.
    """
    
    def __init__(self):
        self.metrics = CacheMetrics()
        self.cache_strategies = {
            CacheStrategy.FREQUENT_DATA: caches['frequent_data'],
            CacheStrategy.EXPENSIVE_CALCULATIONS: caches['expensive_calculations'],
            CacheStrategy.SESSIONS: caches['sessions'],
            CacheStrategy.DEFAULT: cache
        }
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Génère une clé de cache unique et sécurisée.
        
        Args:
            prefix: Préfixe de la clé
            *args: Arguments positionnels
            **kwargs: Arguments nommés
            
        Returns:
            Clé de cache unique
        """
        # Création d'un hash des arguments
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
        
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str, strategy: str = CacheStrategy.DEFAULT) -> Optional[Any]:
        """
        Récupère une valeur du cache.
        
        Args:
            key: Clé de cache
            strategy: Stratégie de cache à utiliser
            
        Returns:
            Valeur en cache ou None
        """
        start_time = time.time()
        
        try:
            cache_backend = self.cache_strategies.get(strategy, cache)
            value = cache_backend.get(key)
            
            if value is not None:
                self.metrics.hits += 1
                structured_logger.system_logger.debug(
                    "Cache hit",
                    key=key,
                    strategy=strategy,
                    event_type="cache_hit"
                )
            else:
                self.metrics.misses += 1
                structured_logger.system_logger.debug(
                    "Cache miss",
                    key=key,
                    strategy=strategy,
                    event_type="cache_miss"
                )
            
            self.metrics.total_time += time.time() - start_time
            return value
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'key': key, 'strategy': strategy},
                error_type="cache_error"
            )
            return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None, 
            strategy: str = CacheStrategy.DEFAULT) -> bool:
        """
        Stocke une valeur dans le cache.
        
        Args:
            key: Clé de cache
            value: Valeur à stocker
            timeout: Timeout en secondes
            strategy: Stratégie de cache à utiliser
            
        Returns:
            True si stockage réussi
        """
        try:
            cache_backend = self.cache_strategies.get(strategy, cache)
            cache_backend.set(key, value, timeout)
            
            self.metrics.sets += 1
            structured_logger.system_logger.debug(
                "Cache set",
                key=key,
                strategy=strategy,
                timeout=timeout,
                event_type="cache_set"
            )
            
            return True
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'key': key, 'strategy': strategy, 'timeout': timeout},
                error_type="cache_error"
            )
            return False
    
    def delete(self, key: str, strategy: str = CacheStrategy.DEFAULT) -> bool:
        """
        Supprime une valeur du cache.
        
        Args:
            key: Clé de cache
            strategy: Stratégie de cache à utiliser
            
        Returns:
            True si suppression réussie
        """
        try:
            cache_backend = self.cache_strategies.get(strategy, cache)
            cache_backend.delete(key)
            
            self.metrics.deletes += 1
            structured_logger.system_logger.debug(
                "Cache delete",
                key=key,
                strategy=strategy,
                event_type="cache_delete"
            )
            
            return True
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'key': key, 'strategy': strategy},
                error_type="cache_error"
            )
            return False
    
    def get_or_set(self, key: str, callable_func: Callable, timeout: Optional[int] = None,
                   strategy: str = CacheStrategy.DEFAULT, *args, **kwargs) -> Any:
        """
        Récupère une valeur du cache ou l'exécute et la met en cache.
        
        Args:
            key: Clé de cache
            callable_func: Fonction à exécuter si pas en cache
            timeout: Timeout en secondes
            strategy: Stratégie de cache à utiliser
            *args: Arguments pour la fonction
            **kwargs: Arguments nommés pour la fonction
            
        Returns:
            Valeur en cache ou résultat de la fonction
        """
        # Tentative de récupération du cache
        cached_value = self.get(key, strategy)
        if cached_value is not None:
            return cached_value
        
        # Exécution de la fonction et mise en cache
        try:
            result = callable_func(*args, **kwargs)
            self.set(key, result, timeout, strategy)
            return result
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'key': key, 'strategy': strategy, 'function': callable_func.__name__},
                error_type="cache_execution_error"
            )
            raise
    
    def invalidate_pattern(self, pattern: str, strategy: str = CacheStrategy.DEFAULT) -> int:
        """
        Invalide toutes les clés correspondant à un pattern.
        
        Args:
            pattern: Pattern de clés à invalider
            strategy: Stratégie de cache à utiliser
            
        Returns:
            Nombre de clés invalidées
        """
        # Note: LocMemCache ne supporte pas les patterns
        # En production, utiliser Redis avec pattern matching
        structured_logger.system_logger.warning(
            "Pattern invalidation not supported with LocMemCache",
            pattern=pattern,
            strategy=strategy,
            event_type="cache_pattern_invalidation"
        )
        return 0
    
    def clear_all(self, strategy: str = CacheStrategy.DEFAULT) -> bool:
        """
        Vide complètement le cache.
        
        Args:
            strategy: Stratégie de cache à utiliser
            
        Returns:
            True si vidage réussi
        """
        try:
            cache_backend = self.cache_strategies.get(strategy, cache)
            cache_backend.clear()
            
            structured_logger.system_logger.info(
                "Cache cleared",
                strategy=strategy,
                event_type="cache_clear"
            )
            
            return True
            
        except Exception as e:
            structured_logger.log_error(
                e,
                {'strategy': strategy},
                error_type="cache_error"
            )
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de performance du cache."""
        return self.metrics.to_dict()
    
    def reset_metrics(self):
        """Remet à zéro les métriques."""
        self.metrics = CacheMetrics()


class QuerySetCache:
    """Cache spécialisé pour les QuerySets Django."""
    
    def __init__(self, cache_service: IntelligentCache):
        self.cache = cache_service
    
    def get_queryset(self, model_class, cache_key: str, timeout: int = 1800,
                     strategy: str = CacheStrategy.FREQUENT_DATA, **filters) -> QuerySet:
        """
        Récupère un QuerySet depuis le cache ou la base de données.
        
        Args:
            model_class: Classe du modèle Django
            cache_key: Clé de cache
            timeout: Timeout en secondes
            strategy: Stratégie de cache
            **filters: Filtres pour le QuerySet
            
        Returns:
            QuerySet mis en cache
        """
        def _fetch_queryset():
            return list(model_class.objects.filter(**filters))
        
        cached_data = self.cache.get_or_set(
            cache_key,
            _fetch_queryset,
            timeout,
            strategy
        )
        
        # Reconstruction du QuerySet depuis les données mises en cache
        return model_class.objects.filter(pk__in=[obj.pk for obj in cached_data])


class UserDataCache:
    """Cache spécialisé pour les données utilisateur."""
    
    def __init__(self, cache_service: IntelligentCache):
        self.cache = cache_service
    
    def get_user_profile(self, user: User) -> Optional[Dict[str, Any]]:
        """
        Récupère le profil utilisateur depuis le cache.
        
        Args:
            user: Utilisateur Django
            
        Returns:
            Profil utilisateur ou None
        """
        cache_key = self.cache._generate_cache_key('user_profile', user.id)
        return self.cache.get(cache_key, CacheStrategy.FREQUENT_DATA)
    
    def set_user_profile(self, user: User, profile_data: Dict[str, Any], 
                        timeout: int = 1800) -> bool:
        """
        Met en cache le profil utilisateur.
        
        Args:
            user: Utilisateur Django
            profile_data: Données du profil
            timeout: Timeout en secondes
            
        Returns:
            True si mise en cache réussie
        """
        cache_key = self.cache._generate_cache_key('user_profile', user.id)
        return self.cache.set(cache_key, profile_data, timeout, CacheStrategy.FREQUENT_DATA)
    
    def invalidate_user_cache(self, user: User) -> bool:
        """
        Invalide le cache d'un utilisateur.
        
        Args:
            user: Utilisateur Django
            
        Returns:
            True si invalidation réussie
        """
        cache_key = self.cache._generate_cache_key('user_profile', user.id)
        return self.cache.delete(cache_key, CacheStrategy.FREQUENT_DATA)


class PerformanceCache:
    """Cache pour les calculs de performance coûteux."""
    
    def __init__(self, cache_service: IntelligentCache):
        self.cache = cache_service
    
    def get_attendance_stats(self, user: User, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les statistiques de présence depuis le cache.
        
        Args:
            user: Utilisateur Django
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Statistiques ou None
        """
        cache_key = self.cache._generate_cache_key(
            'attendance_stats', user.id, start_date, end_date
        )
        return self.cache.get(cache_key, CacheStrategy.EXPENSIVE_CALCULATIONS)
    
    def set_attendance_stats(self, user: User, start_date: str, end_date: str,
                           stats: Dict[str, Any], timeout: int = 3600) -> bool:
        """
        Met en cache les statistiques de présence.
        
        Args:
            user: Utilisateur Django
            start_date: Date de début
            end_date: Date de fin
            stats: Statistiques à mettre en cache
            timeout: Timeout en secondes
            
        Returns:
            True si mise en cache réussie
        """
        cache_key = self.cache._generate_cache_key(
            'attendance_stats', user.id, start_date, end_date
        )
        return self.cache.set(cache_key, stats, timeout, CacheStrategy.EXPENSIVE_CALCULATIONS)
    
    def get_leave_balance(self, user: User, year: int) -> Optional[Dict[str, Any]]:
        """
        Récupère le solde de congés depuis le cache.
        
        Args:
            user: Utilisateur Django
            year: Année
            
        Returns:
            Solde de congés ou None
        """
        cache_key = self.cache._generate_cache_key('leave_balance', user.id, year)
        return self.cache.get(cache_key, CacheStrategy.FREQUENT_DATA)
    
    def set_leave_balance(self, user: User, year: int, balance: Dict[str, Any],
                         timeout: int = 1800) -> bool:
        """
        Met en cache le solde de congés.
        
        Args:
            user: Utilisateur Django
            year: Année
            balance: Solde à mettre en cache
            timeout: Timeout en secondes
            
        Returns:
            True si mise en cache réussie
        """
        cache_key = self.cache._generate_cache_key('leave_balance', user.id, year)
        return self.cache.set(cache_key, balance, timeout, CacheStrategy.FREQUENT_DATA)


# Instances globales des services de cache
intelligent_cache = IntelligentCache()
queryset_cache = QuerySetCache(intelligent_cache)
user_data_cache = UserDataCache(intelligent_cache)
performance_cache = PerformanceCache(intelligent_cache)

