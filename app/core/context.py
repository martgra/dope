import functools
import threading

from pydantic_ai.usage import Usage


def _threadsafe_singleton(cls):
    lock = threading.Lock()

    @functools.wraps(cls)
    def wrapper(*args, **kwargs):
        if not hasattr(cls, "_instance"):
            with lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = cls(*args, **kwargs)
        return cls._instance

    return wrapper


@_threadsafe_singleton
class UsageContext:
    """Global usage context."""

    def __init__(self):
        """Initialize the usage context with thread-safe locking."""
        self._data_lock = threading.Lock()
        self.usage: Usage = Usage()

    def log_usage(self) -> str:
        """Return the total number of tokens spent."""
        print(f"Total tokens used: {self.usage.total_tokens or 0}")
