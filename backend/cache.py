"""Simple in-memory cache for query results."""
import hashlib
import time
from typing import Optional, Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class QueryCache:
    """
    Simple in-memory cache for query results.
    Uses LRU eviction when max size is reached.
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of cached queries
            ttl_seconds: Time to live for cached entries (default 1 hour)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[float, Any]] = {}
        self.access_times: Dict[str, float] = {}

    def _generate_key(self, user_id: int, query_text: str, top_k: int) -> str:
        """Generate cache key from query parameters."""
        key_string = f"{user_id}:{query_text}:{top_k}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(
        self, user_id: int, query_text: str, top_k: int
    ) -> Optional[Tuple[str, List[Dict[str, Any]], float]]:
        """
        Get cached query result.

        Args:
            user_id: User ID
            query_text: Query text
            top_k: Number of results

        Returns:
            Cached result tuple (answer, sources, processing_time) or None
        """
        key = self._generate_key(user_id, query_text, top_k)

        if key in self.cache:
            timestamp, result = self.cache[key]

            # Check if entry is expired
            if time.time() - timestamp > self.ttl_seconds:
                del self.cache[key]
                del self.access_times[key]
                logger.debug(f"Cache entry expired: {key[:8]}...")
                return None

            # Update access time
            self.access_times[key] = time.time()
            logger.info(f"Cache HIT for query: {query_text[:50]}...")
            return result

        logger.debug(f"Cache MISS for query: {query_text[:50]}...")
        return None

    def set(
        self,
        user_id: int,
        query_text: str,
        top_k: int,
        result: Tuple[str, List[Dict[str, Any]], float],
    ):
        """
        Store query result in cache.

        Args:
            user_id: User ID
            query_text: Query text
            top_k: Number of results
            result: Result tuple (answer, sources, processing_time)
        """
        key = self._generate_key(user_id, query_text, top_k)

        # Evict LRU entry if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[lru_key]
            del self.access_times[lru_key]
            logger.debug(f"Evicted LRU cache entry: {lru_key[:8]}...")

        # Store new entry
        self.cache[key] = (time.time(), result)
        self.access_times[key] = time.time()
        logger.debug(f"Cached query result: {query_text[:50]}...")

    def clear(self):
        """Clear all cached entries."""
        self.cache.clear()
        self.access_times.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
        }


# Global cache instance
query_cache = QueryCache(max_size=100, ttl_seconds=3600)
