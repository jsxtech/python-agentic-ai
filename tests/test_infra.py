"""Offline unit tests for pure-logic infrastructure classes.

Covers AgentCache (FIFO eviction), AgentRateLimiter (sliding window),
MemoryManager (bounded growth + keyword search), and planning_agent step
helpers. No network/API calls are made.
"""
from agent_advanced import AgentCache, AgentRateLimiter
from agent_orchestrator import MemoryManager
from planning_agent import _step_description, _step_number, _step_time

# --- AgentCache (FIFO) -----------------------------------------------------

def test_cache_hit_and_miss_counts():
    cache = AgentCache(max_size=10)
    cache.set("a", 1)
    assert cache.get("a") == 1  # hit
    assert cache.get("z") is None  # miss
    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1


def test_cache_fifo_eviction():
    cache = AgentCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # evicts "a" (oldest inserted)
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3
    assert cache.stats()["size"] == 2


def test_cache_update_existing_does_not_evict():
    cache = AgentCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("a", 99)  # update, not insert -> no eviction
    assert cache.get("a") == 99
    assert cache.get("b") == 2


# --- AgentRateLimiter ------------------------------------------------------

def test_rate_limiter_allows_up_to_max():
    limiter = AgentRateLimiter(max_requests=3, window=60)
    assert [limiter.allow_request() for _ in range(4)] == [True, True, True, False]


def test_rate_limiter_time_until_available():
    limiter = AgentRateLimiter(max_requests=1, window=60)
    assert limiter.allow_request() is True
    assert limiter.allow_request() is False
    assert limiter.time_until_available() > 0


def test_rate_limiter_empty_has_zero_wait():
    limiter = AgentRateLimiter(max_requests=5, window=60)
    assert limiter.time_until_available() == 0


# --- MemoryManager ---------------------------------------------------------

def test_memory_store_and_search():
    mm = MemoryManager()
    mm.store("microservices architecture scales well")
    mm.store("monolith deployment is simple")
    results = mm.search("microservices")
    assert len(results) == 1
    assert "microservices" in results[0]["content"]


def test_memory_bounded_growth_evicts_oldest():
    mm = MemoryManager(max_entries=3)
    for i in range(5):
        mm.store(f"unique_token_{i} shared_word")
    # Only the last 3 entries remain.
    assert len(mm.get_all()) == 3
    contents = [m["content"] for m in mm.get_all()]
    assert any("unique_token_4" in c for c in contents)
    assert not any("unique_token_0" in c for c in contents)


def test_memory_index_pruned_after_eviction():
    mm = MemoryManager(max_entries=2)
    mm.store("alpha keyword_zero")
    mm.store("bravo keyword_one")
    mm.store("charlie keyword_two")  # evicts the "alpha" entry
    # Searching the evicted entry's unique keyword yields nothing, and the
    # index no longer references the dropped id.
    assert mm.search("keyword_zero") == []
    assert "keyword_zero" not in mm.index


def test_memory_search_valid_after_eviction():
    mm = MemoryManager(max_entries=2)
    mm.store("first entry token_a")
    mm.store("second entry token_b")
    mm.store("third entry token_c")
    # search must not raise despite id != list-position after eviction
    res = mm.search("token_c")
    assert len(res) == 1
    assert "token_c" in res[0]["content"]


# --- planning_agent step helpers ------------------------------------------

def test_step_number_variants():
    assert _step_number({"step_number": 2}) == "2"
    assert _step_number({"step": 3}) == "3"
    assert _step_number({"number": 4}) == "4"
    assert _step_number({}) == "0"


def test_step_description_variants():
    assert _step_description({"description": "d"}) == "d"
    assert _step_description({"task": "t"}) == "t"
    assert _step_description({"desc": "x"}) == "x"


def test_step_time_variants():
    assert _step_time({"estimated_time": "5m"}) == "5m"
    assert _step_time({"time": "1h"}) == "1h"
    assert _step_time({}) == "unknown"
