"""Thread-safe and process-safe file locking for cache operations.

This module provides a context manager for acquiring exclusive locks on cache files
to prevent race conditions when multiple threads or processes access the cache.

Works across platforms:
- Unix/Linux/macOS: Uses fcntl.flock()
- Windows: Uses msvcrt.locking()
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

# Platform-specific imports
if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


class CacheLock:
    """Context manager for acquiring exclusive locks on cache files.

    Usage:
        with CacheLock(cache_path):
            # Perform cache read/write operations
            # Lock is automatically released on exit

    The lock file is created in the same directory as the cache file
    with a .lock extension. Multiple processes can safely wait for
    the lock to be released.
    """

    def __init__(self, cache_path: str, timeout: float = 30.0, poll_interval: float = 0.1):
        """Initialize cache lock.

        Args:
            cache_path: Path to the cache file to lock
            timeout: Maximum seconds to wait for lock (default: 30)
            poll_interval: Seconds between lock acquisition attempts (default: 0.1)
        """
        self.cache_path = Path(cache_path)
        self.lock_path = self.cache_path.parent / f".{self.cache_path.name}.lock"
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.lock_file: Optional[int] = None

    def __enter__(self):
        """Acquire the lock with timeout."""
        start_time = time.time()

        # Ensure lock directory exists
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        while True:
            try:
                # Open/create lock file (must use low-level os.open for proper locking)
                self.lock_file = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR | os.O_TRUNC)

                # Try to acquire exclusive lock
                if sys.platform == "win32":
                    # Windows: Use msvcrt.locking()
                    # LK_NBLCK = non-blocking exclusive lock
                    msvcrt.locking(self.lock_file, msvcrt.LK_NBLCK, 1)
                else:
                    # Unix: Use fcntl.flock()
                    # LOCK_EX | LOCK_NB = exclusive non-blocking lock
                    fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

                # Successfully acquired lock
                return self

            except (OSError, IOError, BlockingIOError) as e:
                # Lock is held by another process
                if self.lock_file is not None:
                    try:
                        os.close(self.lock_file)
                    except Exception:
                        pass
                    self.lock_file = None

                # Check timeout
                elapsed = time.time() - start_time
                if elapsed >= self.timeout:
                    raise TimeoutError(
                        f"Could not acquire lock on {self.cache_path} after {self.timeout}s"
                    ) from e

                # Wait before retrying
                time.sleep(self.poll_interval)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the lock."""
        if self.lock_file is not None:
            try:
                # Release lock (closing the file releases the lock automatically)
                os.close(self.lock_file)
            except Exception:
                pass
            finally:
                self.lock_file = None

            # Clean up lock file (best effort - may fail if another process is waiting)
            try:
                if self.lock_path.exists():
                    self.lock_path.unlink()
            except Exception:
                pass  # Not critical if cleanup fails


class SharedCacheLock:
    """Context manager for acquiring shared (read) locks on cache files.

    Multiple readers can hold shared locks simultaneously, but exclusive
    locks (CacheLock) will wait for all shared locks to be released.

    Usage:
        with SharedCacheLock(cache_path):
            # Perform cache read operations
            # Other readers can also read, but writers must wait
    """

    def __init__(self, cache_path: str, timeout: float = 30.0, poll_interval: float = 0.1):
        """Initialize shared cache lock.

        Args:
            cache_path: Path to the cache file to lock
            timeout: Maximum seconds to wait for lock (default: 30)
            poll_interval: Seconds between lock acquisition attempts (default: 0.1)
        """
        self.cache_path = Path(cache_path)
        self.lock_path = self.cache_path.parent / f".{self.cache_path.name}.lock"
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.lock_file: Optional[int] = None

    def __enter__(self):
        """Acquire the shared lock with timeout."""
        start_time = time.time()

        # Ensure lock directory exists
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)

        while True:
            try:
                # Open/create lock file
                self.lock_file = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR | os.O_TRUNC)

                # Try to acquire shared lock
                if sys.platform == "win32":
                    # Windows doesn't have true shared locks via msvcrt
                    # Fall back to exclusive lock (degraded performance but still safe)
                    msvcrt.locking(self.lock_file, msvcrt.LK_NBLCK, 1)
                else:
                    # Unix: Use fcntl.flock() with LOCK_SH for shared lock
                    fcntl.flock(self.lock_file, fcntl.LOCK_SH | fcntl.LOCK_NB)

                # Successfully acquired lock
                return self

            except (OSError, IOError, BlockingIOError) as e:
                # Lock is held by another process
                if self.lock_file is not None:
                    try:
                        os.close(self.lock_file)
                    except Exception:
                        pass
                    self.lock_file = None

                # Check timeout
                elapsed = time.time() - start_time
                if elapsed >= self.timeout:
                    raise TimeoutError(
                        f"Could not acquire shared lock on {self.cache_path} after {self.timeout}s"
                    ) from e

                # Wait before retrying
                time.sleep(self.poll_interval)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the shared lock."""
        if self.lock_file is not None:
            try:
                os.close(self.lock_file)
            except Exception:
                pass
            finally:
                self.lock_file = None

            # Clean up lock file (best effort)
            try:
                if self.lock_path.exists():
                    self.lock_path.unlink()
            except Exception:
                pass
