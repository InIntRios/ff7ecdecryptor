"""
Aspect-Oriented Programming (AOP) Helpers & Decorators
Provides clean cross-cutting concerns: performance timing, safe error handling, and synchronization.
"""

import time
import functools
import threading
import logging
from typing import Callable, Any, Optional


def timed_action(action_name: str, logger: Optional[logging.Logger] = None) -> Callable:
    """Decorator that measures and logs the elapsed execution time of a function."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            log = logger or logging.getLogger("FF7EC")
            log.debug(f"[AOP:Timer] Starting '{action_name}'...")
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start_time
                log.debug(f"[AOP:Timer] '{action_name}' completed in {elapsed:.3f}s")
                return result
            except Exception as ex:
                elapsed = time.perf_counter() - start_time
                log.error(f"[AOP:Timer] '{action_name}' failed after {elapsed:.3f}s: {ex}")
                raise
        return wrapper
    return decorator


def safe_run(fallback_return: Any = None, logger: Optional[logging.Logger] = None) -> Callable:
    """Decorator that catches unexpected exceptions, logs them, and returns a safe fallback."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                log = logger or logging.getLogger("FF7EC")
                log.warning(f"[AOP:SafeRun] Suppressed exception in {func.__name__}: {ex}")
                return fallback_return
        return wrapper
    return decorator


def thread_synchronized(lock: threading.Lock) -> Callable:
    """Decorator ensuring thread-safe access to a shared resource using the given Lock."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with lock:
                return func(*args, **kwargs)
        return wrapper
    return decorator
