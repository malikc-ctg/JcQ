"""Retry utilities with exponential backoff."""

import time
import logging
from typing import Callable, TypeVar, Optional, List, Type

T = TypeVar("T")
logger = logging.getLogger(__name__)


def retry_with_backoff(
    func: Callable[[], T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry (no arguments)
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each failure
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback called on each retry (exception, attempt_num)
    
    Returns:
        Result of func()
    
    Raises:
        Last exception if all attempts fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts:
                if on_retry:
                    on_retry(e, attempt)
                logger.warning(
                    f"Attempt {attempt}/{max_attempts} failed: {e}. Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_attempts} attempts failed. Last error: {e}")
    
    raise last_exception

