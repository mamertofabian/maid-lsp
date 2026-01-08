"""Debounce utility for handling rapid document changes.

This module provides a Debouncer class that delays and coalesces rapid
function calls, which is essential for handling document change events
in the LSP server without overwhelming the validation system.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")


class Debouncer:
    """Async debouncer for coalescing rapid function calls.

    The debouncer delays execution of a function by a configurable amount of time.
    If the same key is called again before the delay expires, the previous call
    is cancelled and a new delay starts.
    """

    def __init__(self, delay_ms: float = 100.0) -> None:
        """Initialize the debouncer with a delay.

        Args:
            delay_ms: The delay in milliseconds before executing the function.
                     Defaults to 100ms.
        """
        self._delay_seconds = delay_ms / 1000.0
        self._tasks: dict[str, asyncio.Task[Any]] = {}

    async def debounce(self, key: str, func: Callable[[], Awaitable[T]]) -> T:
        """Debounce a function call by key.

        If a call with the same key is already pending, it will be cancelled
        and replaced with this new call.

        Args:
            key: A unique identifier for this debounce group.
            func: An async callable to execute after the delay.

        Returns:
            The result of calling func().

        Raises:
            asyncio.CancelledError: If this call was cancelled by a subsequent call.
        """
        # Cancel any existing task for this key
        if key in self._tasks:
            self._tasks[key].cancel()

        async def _delayed_call() -> T:
            await asyncio.sleep(self._delay_seconds)
            return await func()

        # Create and store the new task
        task: asyncio.Task[T] = asyncio.create_task(_delayed_call())
        self._tasks[key] = task

        try:
            result = await task
            return result
        finally:
            # Clean up the task reference if it's still ours
            if self._tasks.get(key) is task:
                del self._tasks[key]

    def cancel(self, key: str) -> bool:
        """Cancel a pending debounced call.

        Args:
            key: The key of the debounce group to cancel.

        Returns:
            True if a pending task was cancelled, False if no task was pending.
        """
        if key in self._tasks:
            self._tasks[key].cancel()
            del self._tasks[key]
            return True
        return False

    def cancel_all(self) -> None:
        """Cancel all pending debounced calls."""
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
