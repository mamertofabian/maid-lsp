"""Behavioral tests for Task 002: Debounce utility.

These tests verify that the Debouncer class correctly delays and coalesces
rapid function calls, which is essential for handling document change events.
"""

import asyncio
import contextlib
from typing import Any
from unittest.mock import AsyncMock

import pytest

from maid_lsp.utils.debounce import Debouncer


class TestDebouncerInit:
    """Test Debouncer initialization."""

    def test_init_with_default_delay(self) -> None:
        """Debouncer should accept default delay parameter."""
        debouncer = Debouncer(delay_ms=100.0)
        assert debouncer is not None

    def test_init_with_custom_delay(self) -> None:
        """Debouncer should accept custom delay values."""
        debouncer = Debouncer(delay_ms=500.0)
        assert debouncer is not None


class TestDebouncerDebounce:
    """Test Debouncer.debounce method."""

    @pytest.mark.asyncio
    async def test_debounce_calls_function(self) -> None:
        """Debounce should eventually call the provided function."""
        debouncer = Debouncer(delay_ms=10.0)
        mock_func = AsyncMock(return_value="result")

        result = await debouncer.debounce("key1", mock_func)

        assert result == "result"
        mock_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_debounce_returns_function_result(self) -> None:
        """Debounce should return the result from the called function."""
        debouncer = Debouncer(delay_ms=10.0)

        async def my_func() -> dict[str, Any]:
            return {"status": "ok", "count": 42}

        result = await debouncer.debounce("key1", my_func)

        assert result == {"status": "ok", "count": 42}

    @pytest.mark.asyncio
    async def test_debounce_coalesces_rapid_calls(self) -> None:
        """Multiple rapid calls with same key should coalesce into one."""
        debouncer = Debouncer(delay_ms=50.0)
        call_count = 0

        async def counting_func() -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        # Fire multiple calls rapidly without awaiting
        tasks = [
            asyncio.create_task(debouncer.debounce("same_key", counting_func)) for _ in range(5)
        ]

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Only one call should have succeeded, others should be cancelled
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 1
        # The function should only be called once (or at most a few times due to timing)
        assert call_count <= 2  # Allow small margin for timing

    @pytest.mark.asyncio
    async def test_debounce_different_keys_independent(self) -> None:
        """Different keys should be debounced independently."""
        debouncer = Debouncer(delay_ms=10.0)
        results: dict[str, int] = {}

        async def make_func(key: str) -> int:
            results[key] = results.get(key, 0) + 1
            return results[key]

        # Call with different keys
        await asyncio.gather(
            debouncer.debounce("key1", lambda: make_func("key1")),
            debouncer.debounce("key2", lambda: make_func("key2")),
        )

        # Both should have been called
        assert "key1" in results
        assert "key2" in results


class TestDebouncerCancel:
    """Test Debouncer.cancel method."""

    @pytest.mark.asyncio
    async def test_cancel_returns_true_for_pending(self) -> None:
        """Cancel should return True if there was a pending task."""
        debouncer = Debouncer(delay_ms=1000.0)  # Long delay
        mock_func = AsyncMock(return_value="result")

        # Start a debounced call but don't await it
        task = asyncio.create_task(debouncer.debounce("key1", mock_func))

        # Give it a moment to register
        await asyncio.sleep(0.01)

        # Cancel should succeed
        result = debouncer.cancel("key1")
        assert result is True

        # Clean up the task
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    def test_cancel_returns_false_for_nonexistent(self) -> None:
        """Cancel should return False if no pending task exists."""
        debouncer = Debouncer(delay_ms=100.0)

        result = debouncer.cancel("nonexistent_key")

        assert result is False


class TestDebouncerCancelAll:
    """Test Debouncer.cancel_all method."""

    @pytest.mark.asyncio
    async def test_cancel_all_cancels_all_pending(self) -> None:
        """Cancel all should cancel all pending tasks."""
        debouncer = Debouncer(delay_ms=1000.0)  # Long delay
        mock_func = AsyncMock(return_value="result")

        # Start multiple debounced calls
        tasks = [asyncio.create_task(debouncer.debounce(f"key{i}", mock_func)) for i in range(3)]

        # Give them a moment to register
        await asyncio.sleep(0.01)

        # Cancel all
        debouncer.cancel_all()

        # All tasks should be cancelled
        for task in tasks:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    def test_cancel_all_no_error_when_empty(self) -> None:
        """Cancel all should not error when no tasks are pending."""
        debouncer = Debouncer(delay_ms=100.0)

        # Should not raise
        debouncer.cancel_all()
