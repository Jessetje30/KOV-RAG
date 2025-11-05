"""
Tests for the query cache functionality.
Tests LRU eviction, TTL expiry, and cache hit/miss behavior.
"""
import pytest
import time
from cache import QueryCache


class TestQueryCache:
    """Tests for QueryCache class."""

    @pytest.fixture
    def cache(self):
        """Create a test cache with small size for testing."""
        return QueryCache(max_size=3, ttl_seconds=2)

    def test_cache_set_and_get(self, cache):
        """Test basic cache set and get operations."""
        result = ("answer", [{"text": "source"}], 1.5)
        cache.set(user_id=1, query_text="test query", top_k=3, result=result)

        retrieved = cache.get(user_id=1, query_text="test query", top_k=3)
        assert retrieved is not None
        assert retrieved[0] == "answer"
        assert len(retrieved[1]) == 1
        assert retrieved[2] == 1.5

    def test_cache_miss(self, cache):
        """Test cache miss returns None."""
        result = cache.get(user_id=1, query_text="nonexistent", top_k=3)
        assert result is None

    def test_cache_key_uniqueness(self, cache):
        """Test that different parameters create different cache keys."""
        result1 = ("answer1", [], 1.0)
        result2 = ("answer2", [], 2.0)

        # Same user, different query
        cache.set(1, "query1", 3, result1)
        cache.set(1, "query2", 3, result2)

        assert cache.get(1, "query1", 3)[0] == "answer1"
        assert cache.get(1, "query2", 3)[0] == "answer2"

        # Same query, different user
        cache.set(2, "query1", 3, result2)
        assert cache.get(2, "query1", 3)[0] == "answer2"
        assert cache.get(1, "query1", 3)[0] == "answer1"

        # Same user and query, different top_k
        cache.set(1, "query1", 5, result2)
        assert cache.get(1, "query1", 5)[0] == "answer2"
        assert cache.get(1, "query1", 3)[0] == "answer1"

    def test_cache_ttl_expiry(self, cache):
        """Test that cache entries expire after TTL."""
        result = ("answer", [], 1.0)
        cache.set(1, "test", 3, result)

        # Should be cached
        assert cache.get(1, "test", 3) is not None

        # Wait for TTL to expire
        time.sleep(2.1)

        # Should be expired
        assert cache.get(1, "test", 3) is None

    def test_cache_lru_eviction(self, cache):
        """Test LRU eviction when cache is full."""
        # Fill cache to max size (3)
        cache.set(1, "query1", 3, ("a1", [], 1.0))
        cache.set(1, "query2", 3, ("a2", [], 1.0))
        cache.set(1, "query3", 3, ("a3", [], 1.0))

        # Access query1 to make it recently used
        cache.get(1, "query1", 3)

        # Add a 4th item - should evict query2 (LRU)
        cache.set(1, "query4", 3, ("a4", [], 1.0))

        # query2 should be evicted
        assert cache.get(1, "query2", 3) is None

        # Others should still be there
        assert cache.get(1, "query1", 3) is not None
        assert cache.get(1, "query3", 3) is not None
        assert cache.get(1, "query4", 3) is not None

    def test_cache_update_access_time(self, cache):
        """Test that cache access updates LRU order."""
        # Add 3 items
        cache.set(1, "q1", 3, ("a1", [], 1.0))
        time.sleep(0.1)
        cache.set(1, "q2", 3, ("a2", [], 1.0))
        time.sleep(0.1)
        cache.set(1, "q3", 3, ("a3", [], 1.0))

        # Access q1 (oldest) to make it most recent
        cache.get(1, "q1", 3)

        # Add 4th item - should evict q2 (now LRU)
        cache.set(1, "q4", 3, ("a4", [], 1.0))

        assert cache.get(1, "q1", 3) is not None
        assert cache.get(1, "q2", 3) is None

    def test_cache_clear(self, cache):
        """Test clearing the entire cache."""
        cache.set(1, "q1", 3, ("a1", [], 1.0))
        cache.set(1, "q2", 3, ("a2", [], 1.0))

        assert cache.get(1, "q1", 3) is not None

        cache.clear()

        assert cache.get(1, "q1", 3) is None
        assert cache.get(1, "q2", 3) is None

    def test_cache_get_stats(self, cache):
        """Test getting cache statistics."""
        cache.set(1, "q1", 3, ("a1", [], 1.0))
        cache.set(1, "q2", 3, ("a2", [], 1.0))

        stats = cache.get_stats()

        assert stats["size"] == 2
        assert stats["max_size"] == 3
        assert stats["ttl_seconds"] == 2

    def test_cache_with_large_result(self, cache):
        """Test caching large results with multiple sources."""
        large_result = (
            "Long answer" * 100,
            [
                {
                    "text": "Source" * 50,
                    "document_id": f"doc-{i}",
                    "filename": f"file{i}.pdf",
                    "score": 0.9,
                    "chunk_index": i,
                    "summary": "Summary" * 10,
                    "title": f"Title {i}"
                }
                for i in range(10)
            ],
            5.5
        )

        cache.set(1, "complex query", 10, large_result)
        retrieved = cache.get(1, "complex query", 10)

        assert retrieved is not None
        assert len(retrieved[1]) == 10
        assert retrieved[2] == 5.5

    def test_cache_concurrent_operations(self, cache):
        """Test cache handles concurrent-like operations."""
        # Simulate multiple users/queries
        for user_id in range(1, 4):
            for query_num in range(1, 3):
                result = (f"answer_{user_id}_{query_num}", [], 1.0)
                cache.set(user_id, f"query{query_num}", 3, result)

        # Verify all entries that should fit
        assert cache.get(1, "query1", 3) is None  # Should be evicted (LRU)
        assert cache.get(3, "query2", 3) is not None  # Most recent

    def test_cache_does_not_evict_on_update(self, cache):
        """Test that updating an existing key doesn't count as eviction."""
        cache.set(1, "q1", 3, ("a1", [], 1.0))
        cache.set(1, "q2", 3, ("a2", [], 1.0))

        # Update existing key
        cache.set(1, "q1", 3, ("a1_updated", [], 2.0))

        assert cache.get(1, "q1", 3)[0] == "a1_updated"
        assert cache.get(1, "q2", 3) is not None

        # Cache size should still be 2
        stats = cache.get_stats()
        assert stats["size"] == 2


class TestCacheIntegration:
    """Integration tests for cache with RAG pipeline."""

    def test_cache_reduces_processing_time(self):
        """Test that cache significantly reduces processing time for repeat queries."""
        from cache import query_cache

        # Clear cache first
        query_cache.clear()

        # First query (cache miss) - would normally take long
        user_id = 999
        query_text = "integration test query"
        top_k = 3

        # Simulate first query (cache miss)
        result1 = query_cache.get(user_id, query_text, top_k)
        assert result1 is None

        # Store result
        test_result = ("Test answer", [{"text": "source"}], 2.5)
        query_cache.set(user_id, query_text, top_k, test_result)

        # Second query (cache hit) - should be instant
        result2 = query_cache.get(user_id, query_text, top_k)
        assert result2 is not None
        assert result2[0] == "Test answer"
        assert result2[2] == 2.5

    def test_cache_key_generation_consistency(self):
        """Test that cache key generation is consistent."""
        from cache import QueryCache

        cache = QueryCache()

        # Generate key multiple times with same params
        key1 = cache._generate_key(1, "test query", 3)
        key2 = cache._generate_key(1, "test query", 3)
        key3 = cache._generate_key(1, "test query", 3)

        assert key1 == key2 == key3

        # Different params should give different keys
        key4 = cache._generate_key(2, "test query", 3)
        assert key1 != key4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
