"""
Caching utilities for Data Insights application.
Provides in-memory caching for filter values and common queries to improve performance.
"""

import functools
import time
import logging
from typing import Any, Dict, Optional, Callable
from threading import Lock
import hashlib
import json

logger = logging.getLogger(__name__)

class ApplicationCache:
    """
    Thread-safe in-memory cache for application data.
    Uses TTL (time-to-live) for automatic cache expiration.
    """
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default TTL
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if a cache entry has expired."""
        return time.time() > cache_entry['expires_at']
    
    def _clean_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items() 
            if current_time > entry['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not self._is_expired(entry):
                    logger.debug(f"Cache HIT for key: {key}")
                    return entry['value']
                else:
                    # Remove expired entry
                    del self._cache[key]
                    logger.debug(f"Cache EXPIRED for key: {key}")
            
            logger.debug(f"Cache MISS for key: {key}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL override."""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            logger.debug(f"Cache SET for key: {key}, TTL: {ttl}s")
            
            # Periodic cleanup
            if len(self._cache) % 50 == 0:  # Clean every 50 entries
                self._clean_expired()
    
    def delete(self, key: str) -> bool:
        """Delete specific key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache DELETE for key: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache CLEARED")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            self._clean_expired()
            return {
                'total_entries': len(self._cache),
                'cache_size_mb': len(str(self._cache)) / 1024 / 1024,
                'oldest_entry': min(
                    [entry['created_at'] for entry in self._cache.values()],
                    default=time.time()
                ),
                'keys': list(self._cache.keys())
            }

# Global cache instance
_app_cache = ApplicationCache(default_ttl=600)  # 10 minutes for filter data


def get_cache_key(prefix: str, **kwargs) -> str:
    """
    Generate a consistent cache key from prefix and parameters.
    
    Args:
        prefix: Cache key prefix (e.g., 'filter_values', 'naics_data')
        **kwargs: Parameters to include in the cache key
    
    Returns:
        String cache key
    """
    # Sort kwargs for consistent key generation
    sorted_params = sorted(kwargs.items())
    params_str = json.dumps(sorted_params, sort_keys=True, default=str)
    
    # Create hash for long parameter strings
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
    
    return f"{prefix}:{params_hash}"


def cached_query(ttl: int = 300, key_prefix: str = "query"):
    """
    Decorator for caching query results.
    
    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache key
    
    Example:
        @cached_query(ttl=600, key_prefix="filter_values")
        def get_unique_agencies():
            # expensive query
            return result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = get_cache_key(
                f"{key_prefix}:{func.__name__}",
                args=args,
                kwargs=kwargs
            )
            
            # Try to get from cache first
            cached_result = _app_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            _app_cache.set(cache_key, result, ttl)
            
            logger.info(f"Function {func.__name__} executed in {execution_time:.2f}s, result cached with TTL {ttl}s")
            return result
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.
    
    Args:
        pattern: Pattern to match against cache keys
    
    Returns:
        Number of entries invalidated
    """
    with _app_cache._lock:
        keys_to_delete = [
            key for key in _app_cache._cache.keys() 
            if pattern in key
        ]
        
        for key in keys_to_delete:
            del _app_cache._cache[key]
        
        logger.info(f"Invalidated {len(keys_to_delete)} cache entries matching pattern: {pattern}")
        return len(keys_to_delete)


def get_cache_stats() -> Dict[str, Any]:
    """Get current cache statistics."""
    return _app_cache.stats()


def clear_all_cache() -> None:
    """Clear all cache entries."""
    _app_cache.clear()


# Convenience functions for common cache operations
def cache_filter_values(func: Callable) -> Callable:
    """Decorator specifically for filter value functions with 10-minute TTL."""
    return cached_query(ttl=600, key_prefix="filter_values")(func)


def cache_dashboard_data(func: Callable) -> Callable:
    """Decorator specifically for dashboard data with 5-minute TTL."""
    return cached_query(ttl=300, key_prefix="dashboard_data")(func)


def cache_summary_metrics(func: Callable) -> Callable:
    """Decorator specifically for summary metrics with 2-minute TTL."""
    return cached_query(ttl=120, key_prefix="summary_metrics")(func)
