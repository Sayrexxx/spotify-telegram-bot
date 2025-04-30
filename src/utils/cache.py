import time
from functools import wraps
from typing import Callable, Any, Dict, Tuple

_cache: Dict[Tuple[str, Tuple[Any, ...], frozenset], Tuple[Any, float]] = {}


def cache_res(ttl: int = 60) -> Callable:
    """
    A decorator for caching function results in memory.
    - ttl: Time-to-live for cached items, in seconds.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapped(*args, **kwargs):
            key = (func.__name__, args, frozenset(kwargs.items()))
            if key in _cache:
                value, timestamp = _cache[key]
                if time.time() - timestamp < ttl:
                    return value
            result = func(*args, **kwargs)
            _cache[key] = (result, time.time())
            return result

        return wrapped

    return decorator
