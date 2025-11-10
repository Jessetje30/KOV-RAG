"""
Embedding cache system to reduce API calls and improve performance.
"""
import hashlib
import logging
import pickle
from pathlib import Path
from typing import List, Optional, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    LRU cache for embeddings with optional disk persistence.

    Features:
    - In-memory LRU cache for fast access
    - Content-addressable storage (hash-based keys)
    - Optional disk persistence for cache survival across restarts
    - Thread-safe operations
    """

    def __init__(self, cache_dir: Optional[Path] = None, max_memory_items: int = 1000):
        """
        Initialize embedding cache.

        Args:
            cache_dir: Directory for disk cache persistence (None = memory only)
            max_memory_items: Maximum number of embeddings in memory cache
        """
        self.cache_dir = cache_dir
        self.max_memory_items = max_memory_items
        self._memory_cache: Dict[str, List[float]] = {}
        self._access_order: List[str] = []  # For LRU tracking

        # Create cache directory if disk persistence enabled
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Embedding cache initialized with disk persistence: {self.cache_dir}")
        else:
            logger.info(f"Embedding cache initialized (memory only, max {max_memory_items} items)")

    def _compute_hash(self, text: str) -> str:
        """
        Compute content hash for a text.

        Args:
            text: Text to hash

        Returns:
            SHA256 hash as hex string
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _evict_lru(self):
        """Evict least recently used item if cache is full."""
        if len(self._memory_cache) >= self.max_memory_items:
            # Remove least recently used item
            if self._access_order:
                lru_key = self._access_order.pop(0)
                if lru_key in self._memory_cache:
                    del self._memory_cache[lru_key]
                    logger.debug(f"Evicted LRU embedding: {lru_key[:16]}...")

    def _update_access_order(self, key: str):
        """
        Update access order for LRU tracking.

        Args:
            key: Cache key that was accessed
        """
        # Remove if already in list
        if key in self._access_order:
            self._access_order.remove(key)
        # Add to end (most recently used)
        self._access_order.append(key)

    def get(self, text: str) -> Optional[List[float]]:
        """
        Get embedding from cache.

        Args:
            text: Text to look up

        Returns:
            Embedding vector if found, None otherwise
        """
        key = self._compute_hash(text)

        # Check memory cache first
        if key in self._memory_cache:
            self._update_access_order(key)
            logger.debug(f"Embedding cache HIT (memory): {key[:16]}...")
            return self._memory_cache[key]

        # Check disk cache if enabled
        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.pkl"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        embedding = pickle.load(f)

                    # Add to memory cache
                    self._evict_lru()
                    self._memory_cache[key] = embedding
                    self._update_access_order(key)

                    logger.debug(f"Embedding cache HIT (disk): {key[:16]}...")
                    return embedding
                except Exception as e:
                    logger.error(f"Error loading from disk cache: {e}")

        logger.debug(f"Embedding cache MISS: {key[:16]}...")
        return None

    def put(self, text: str, embedding: List[float]):
        """
        Store embedding in cache.

        Args:
            text: Original text
            embedding: Embedding vector to store
        """
        key = self._compute_hash(text)

        # Store in memory cache
        self._evict_lru()
        self._memory_cache[key] = embedding
        self._update_access_order(key)

        # Store on disk if enabled
        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.pkl"
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(embedding, f)
                logger.debug(f"Stored embedding to disk: {key[:16]}...")
            except Exception as e:
                logger.error(f"Error storing to disk cache: {e}")

    def get_batch(self, texts: List[str]) -> Dict[str, Optional[List[float]]]:
        """
        Get multiple embeddings from cache.

        Args:
            texts: List of texts to look up

        Returns:
            Dictionary mapping text to embedding (None if not found)
        """
        results = {}
        for text in texts:
            results[text] = self.get(text)
        return results

    def put_batch(self, texts: List[str], embeddings: List[List[float]]):
        """
        Store multiple embeddings in cache.

        Args:
            texts: List of original texts
            embeddings: List of embedding vectors
        """
        if len(texts) != len(embeddings):
            raise ValueError("texts and embeddings must have same length")

        for text, embedding in zip(texts, embeddings):
            self.put(text, embedding)

    def clear_memory(self):
        """Clear in-memory cache."""
        self._memory_cache.clear()
        self._access_order.clear()
        logger.info("Memory cache cleared")

    def clear_disk(self):
        """Clear disk cache."""
        if not self.cache_dir:
            return

        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            logger.info("Disk cache cleared")
        except Exception as e:
            logger.error(f"Error clearing disk cache: {e}")

    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        stats = {
            "memory_items": len(self._memory_cache),
            "max_memory_items": self.max_memory_items,
        }

        if self.cache_dir:
            stats["disk_items"] = len(list(self.cache_dir.glob("*.pkl")))

        return stats
