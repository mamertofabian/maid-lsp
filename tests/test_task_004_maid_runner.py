"""Behavioral tests for Task 004: MaidRunner Library Wrapper.

These tests verify that the MaidRunner class correctly wraps the maid-runner
library for validation operations. Library calls are mocked to test the wrapper
behavior in isolation.
"""

import asyncio
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from maid_lsp.validation.models import ValidationMode, ValidationResult
from maid_lsp.validation.runner import MaidRunner


class TestMaidRunnerInit:
    """Test MaidRunner initialization."""

    def test_init_with_defaults(self) -> None:
        """MaidRunner should be instantiable with default parameters."""
        runner = MaidRunner()
        assert runner is not None

    def test_init_with_custom_timeout(self) -> None:
        """MaidRunner should accept custom timeout value."""
        runner = MaidRunner(timeout=60.0)
        assert runner is not None

    def test_init_explicit_call(self) -> None:
        """MaidRunner.__init__ should initialize the instance properly."""
        runner = MaidRunner.__new__(MaidRunner)
        MaidRunner.__init__(runner, timeout=30.0)
        assert runner is not None


class TestMaidRunnerValidate:
    """Test MaidRunner.validate method."""

    @pytest.mark.asyncio
    async def test_validate_returns_validation_result(self) -> None:
        """Validate should return a ValidationResult object."""
        runner = MaidRunner()
        manifest_path = Path("/path/to/test.manifest.json")

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "success": True,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        with patch("maid_lsp.validation.runner.maid_validate", return_value=mock_result):
            result = await runner.validate(manifest_path, ValidationMode.BEHAVIORAL)

        assert isinstance(result, ValidationResult)

    @pytest.mark.asyncio
    async def test_validate_with_behavioral_mode(self) -> None:
        """Validate should pass behavioral mode to the library."""
        runner = MaidRunner()
        manifest_path = Path("/path/to/test.manifest.json")

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "success": True,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        with patch(
            "maid_lsp.validation.runner.maid_validate", return_value=mock_result
        ) as mock_validate:
            result = await runner.validate(manifest_path, ValidationMode.BEHAVIORAL)

            mock_validate.assert_called_once()
            call_kwargs = mock_validate.call_args
            assert call_kwargs.kwargs["mode"].value == "behavioral"

        assert result.success is True

    @pytest.mark.asyncio
    async def test_validate_with_implementation_mode(self) -> None:
        """Validate should pass implementation mode to the library."""
        runner = MaidRunner()
        manifest_path = Path("/path/to/test.manifest.json")

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "success": True,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        with patch(
            "maid_lsp.validation.runner.maid_validate", return_value=mock_result
        ) as mock_validate:
            result = await runner.validate(manifest_path, ValidationMode.IMPLEMENTATION)

            mock_validate.assert_called_once()
            call_kwargs = mock_validate.call_args
            assert call_kwargs.kwargs["mode"].value == "implementation"

        assert result.success is True

    @pytest.mark.asyncio
    async def test_validate_success_true_for_passing_validation(self) -> None:
        """Validate should return success=True when validation passes."""
        runner = MaidRunner()
        manifest_path = Path("/path/to/valid.manifest.json")

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "success": True,
            "errors": [],
            "warnings": [],
            "metadata": {"duration_ms": 50},
        }

        with patch("maid_lsp.validation.runner.maid_validate", return_value=mock_result):
            result = await runner.validate(manifest_path, ValidationMode.BEHAVIORAL)

        assert result.success is True
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_validate_success_false_with_errors(self) -> None:
        """Validate should return success=False when there are errors."""
        runner = MaidRunner()
        manifest_path = Path("/path/to/invalid.manifest.json")

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "success": False,
            "errors": [
                {
                    "code": "E001",
                    "message": "Missing required field",
                    "file": "/path/to/invalid.manifest.json",
                    "line": 5,
                    "column": 1,
                    "severity": "error",
                }
            ],
            "warnings": [],
            "metadata": {},
        }

        with patch("maid_lsp.validation.runner.maid_validate", return_value=mock_result):
            result = await runner.validate(manifest_path, ValidationMode.BEHAVIORAL)

        assert result.success is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "E001"

    @pytest.mark.asyncio
    async def test_validate_includes_warnings(self) -> None:
        """Validate should include warnings in the result."""
        runner = MaidRunner()
        manifest_path = Path("/path/to/test.manifest.json")

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "success": True,
            "errors": [],
            "warnings": [
                {
                    "code": "W001",
                    "message": "Deprecated field",
                    "file": "/path/to/test.manifest.json",
                    "line": 10,
                    "column": 5,
                    "severity": "warning",
                }
            ],
            "metadata": {},
        }

        with patch("maid_lsp.validation.runner.maid_validate", return_value=mock_result):
            result = await runner.validate(manifest_path, ValidationMode.BEHAVIORAL)

        assert result.success is True
        assert len(result.warnings) == 1
        assert result.warnings[0].code == "W001"

    @pytest.mark.asyncio
    async def test_validate_includes_metadata(self) -> None:
        """Validate should include metadata in the result."""
        runner = MaidRunner()
        manifest_path = Path("/path/to/test.manifest.json")

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "success": True,
            "errors": [],
            "warnings": [],
            "metadata": {"duration_ms": 150, "version": "1.0.0"},
        }

        with patch("maid_lsp.validation.runner.maid_validate", return_value=mock_result):
            result = await runner.validate(manifest_path, ValidationMode.BEHAVIORAL)

        assert result.metadata["duration_ms"] == 150
        assert result.metadata["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_validate_uses_manifest_path(self) -> None:
        """Validate should pass manifest_path to the library."""
        runner = MaidRunner()
        manifest_path = Path("/specific/path/to/manifest.json")

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "success": True,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        with patch(
            "maid_lsp.validation.runner.maid_validate", return_value=mock_result
        ) as mock_validate:
            await runner.validate(manifest_path, ValidationMode.BEHAVIORAL)

            mock_validate.assert_called_once()
            call_args = mock_validate.call_args
            assert call_args.args[0] == str(manifest_path)

    @pytest.mark.asyncio
    async def test_validate_passes_use_chain(self) -> None:
        """Validate should pass use_chain=True to the library."""
        runner = MaidRunner()
        manifest_path = Path("/path/to/test.manifest.json")

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "success": True,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        with patch(
            "maid_lsp.validation.runner.maid_validate", return_value=mock_result
        ) as mock_validate:
            await runner.validate(manifest_path, ValidationMode.BEHAVIORAL)

            assert mock_validate.call_args.kwargs["use_chain"] is True


class TestMaidRunnerValidateTimeout:
    """Test MaidRunner.validate timeout handling."""

    @pytest.mark.asyncio
    async def test_validate_timeout_raises_exception(self) -> None:
        """Validate should raise an exception on timeout."""
        runner = MaidRunner(timeout=0.01)

        def slow_validate(*_args: object, **_kwargs: object) -> MagicMock:
            time.sleep(5)
            return MagicMock()

        with (
            patch("maid_lsp.validation.runner.maid_validate", side_effect=slow_validate),
            pytest.raises(asyncio.TimeoutError),
        ):
            await runner.validate(Path("/path/to/test.manifest.json"), ValidationMode.BEHAVIORAL)

    @pytest.mark.asyncio
    async def test_validate_respects_custom_timeout(self) -> None:
        """Validate should respect the configured timeout value."""
        custom_timeout = 30.0
        runner = MaidRunner(timeout=custom_timeout)
        manifest_path = Path("/path/to/test.manifest.json")

        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "success": True,
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        with patch("maid_lsp.validation.runner.maid_validate", return_value=mock_result):
            result = await runner.validate(manifest_path, ValidationMode.BEHAVIORAL)

        assert isinstance(result, ValidationResult)


class TestMaidRunnerValidateErrorHandling:
    """Test MaidRunner.validate error handling."""

    @pytest.mark.asyncio
    async def test_validate_handles_library_exception(self) -> None:
        """Validate should propagate exceptions from the library."""
        runner = MaidRunner()
        manifest_path = Path("/path/to/test.manifest.json")

        with (
            patch(
                "maid_lsp.validation.runner.maid_validate",
                side_effect=RuntimeError("Validation failed"),
            ),
            pytest.raises(RuntimeError, match="Validation failed"),
        ):
            await runner.validate(manifest_path, ValidationMode.BEHAVIORAL)

    @pytest.mark.asyncio
    async def test_validate_handles_file_not_found(self) -> None:
        """Validate should propagate FileNotFoundError from the library."""
        runner = MaidRunner()
        manifest_path = Path("/path/to/nonexistent.manifest.json")

        with (
            patch(
                "maid_lsp.validation.runner.maid_validate",
                side_effect=FileNotFoundError("Manifest not found"),
            ),
            pytest.raises(FileNotFoundError),
        ):
            await runner.validate(manifest_path, ValidationMode.BEHAVIORAL)


class TestMaidRunnerFindManifests:
    """Test MaidRunner.find_manifests method."""

    @pytest.mark.asyncio
    async def test_find_manifests_returns_list_of_paths(self) -> None:
        """Find manifests should return a list of Path objects."""
        runner = MaidRunner()
        file_path = Path("/path/to/source/file.py")

        mock_chain = MagicMock()
        mock_chain.manifests_for_file.return_value = [
            "/path/to/task-001.manifest.json",
            "/path/to/task-002.manifest.json",
        ]

        with patch("maid_lsp.validation.runner.ManifestChain", return_value=mock_chain):
            result = await runner.find_manifests(file_path)

        assert isinstance(result, list)
        assert all(isinstance(p, Path) for p in result)

    @pytest.mark.asyncio
    async def test_find_manifests_empty_for_no_matches(self) -> None:
        """Find manifests should return empty list when no manifests found."""
        runner = MaidRunner()
        file_path = Path("/path/to/unrelated/file.txt")

        mock_chain = MagicMock()
        mock_chain.manifests_for_file.return_value = []

        with patch("maid_lsp.validation.runner.ManifestChain", return_value=mock_chain):
            result = await runner.find_manifests(file_path)

        assert result == []

    @pytest.mark.asyncio
    async def test_find_manifests_returns_correct_paths(self) -> None:
        """Find manifests should return the correct manifest paths."""
        runner = MaidRunner()
        file_path = Path("/project/src/module.py")

        expected_paths = [
            "/project/manifests/task-001.manifest.json",
            "/project/manifests/task-002.manifest.json",
        ]

        mock_chain = MagicMock()
        mock_chain.manifests_for_file.return_value = expected_paths

        with patch("maid_lsp.validation.runner.ManifestChain", return_value=mock_chain):
            result = await runner.find_manifests(file_path)

        assert len(result) == 2
        assert result[0] == Path(expected_paths[0])
        assert result[1] == Path(expected_paths[1])

    @pytest.mark.asyncio
    async def test_find_manifests_uses_file_path(self) -> None:
        """Find manifests should pass file_path to ManifestChain."""
        runner = MaidRunner()
        file_path = Path("/specific/source/file.py")

        mock_chain = MagicMock()
        mock_chain.manifests_for_file.return_value = []

        with patch("maid_lsp.validation.runner.ManifestChain", return_value=mock_chain):
            await runner.find_manifests(file_path)

            mock_chain.manifests_for_file.assert_called_once_with(str(file_path))

    @pytest.mark.asyncio
    async def test_find_manifests_handles_single_manifest(self) -> None:
        """Find manifests should handle a single manifest correctly."""
        runner = MaidRunner()
        file_path = Path("/project/src/main.py")

        mock_chain = MagicMock()
        mock_chain.manifests_for_file.return_value = ["/project/manifests/task-001.manifest.json"]

        with patch("maid_lsp.validation.runner.ManifestChain", return_value=mock_chain):
            result = await runner.find_manifests(file_path)

        assert len(result) == 1
        assert result[0] == Path("/project/manifests/task-001.manifest.json")
