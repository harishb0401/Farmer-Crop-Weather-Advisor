"""Timing and performance instrumentation utility using time.perf_counter()."""
import time
import functools
import inspect
import threading
from typing import Optional, Dict, List

# Thread-local storage for tracking timings per request
_local_timings = threading.local()


def reset_timings():
    """Reset timing records for a new request."""
    _local_timings.records = []


def record_timing(name: str, duration: float):
    """Store a timing record."""
    if not hasattr(_local_timings, "records"):
        _local_timings.records = []
    _local_timings.records.append((name, duration))


def get_timings() -> List[tuple]:
    """Retrieve recorded timings."""
    return getattr(_local_timings, "records", [])


class TimedBlock:
    """Context manager for timing code blocks."""
    def __init__(self, name: str, start_emoji: str = "⏳", success_emoji: str = "✅"):
        self.name = name
        self.start_emoji = start_emoji
        self.success_emoji = success_emoji
        self.start_time = 0.0

    def __enter__(self):
        print(f"\n{self.start_emoji} [{self.name}] started...", flush=True)
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        if exc_type is not None:
            print(f"❌ [{self.name}] failed after {elapsed:.2f}s", flush=True)
        else:
            record_timing(self.name, elapsed)
            print(f"{self.success_emoji} [{self.name}] completed in {elapsed:.2f}s", flush=True)
        return False  # Do not suppress exceptions


def timed_operation(name: str, start_emoji: str = "⏳", success_emoji: str = "✅"):
    """
    Decorator for timing synchronous or asynchronous functions.
    
    Usage:
        @timed_operation("Supervisor Agent")
        def supervisor_node(state): ...
    """
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                print(f"\n{start_emoji} [{name}] started...", flush=True)
                start_time = time.perf_counter()
                try:
                    res = await func(*args, **kwargs)
                    elapsed = time.perf_counter() - start_time
                    record_timing(name, elapsed)
                    print(f"{success_emoji} [{name}] completed in {elapsed:.2f}s", flush=True)
                    return res
                except Exception:
                    elapsed = time.perf_counter() - start_time
                    print(f"❌ [{name}] failed after {elapsed:.2f}s", flush=True)
                    raise
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                print(f"\n{start_emoji} [{name}] started...", flush=True)
                start_time = time.perf_counter()
                try:
                    res = func(*args, **kwargs)
                    elapsed = time.perf_counter() - start_time
                    record_timing(name, elapsed)
                    print(f"{success_emoji} [{name}] completed in {elapsed:.2f}s", flush=True)
                    return res
                except Exception:
                    elapsed = time.perf_counter() - start_time
                    print(f"❌ [{name}] failed after {elapsed:.2f}s", flush=True)
                    raise
            return sync_wrapper
    return decorator


def start_request_timer() -> float:
    """Print request start header and return start counter."""
    reset_timings()
    print("\n" + "=" * 50, flush=True)
    print("🚀 NEW REQUEST", flush=True)
    print("=" * 50, flush=True)
    return time.perf_counter()


def stop_request_timer(start_time: float):
    """Print total request time and compact summary table."""
    total_elapsed = time.perf_counter() - start_time
    print("\n" + "=" * 50, flush=True)
    print(f"🏁 TOTAL REQUEST TIME: {total_elapsed:.2f}s", flush=True)
    print("=" * 50, flush=True)

    records = get_timings()
    if records:
        print("\nPerformance Summary")
        print("-------------------")
        for item_name, dur in records:
            print(f"{item_name:<18}: {dur:.2f}s")
        print("-------------------")
        print(f"{'TOTAL':<18}: {total_elapsed:.2f}s\n", flush=True)
