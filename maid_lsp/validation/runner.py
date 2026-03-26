"""Async wrapper for maid-runner library.

This module provides the MaidRunner class that wraps the maid-runner library
for validation operations using asyncio thread execution.
"""

import asyncio
from pathlib import Path

from maid_runner import ManifestChain
from maid_runner import ValidationMode as MaidValidationMode
from maid_runner import validate as maid_validate

from maid_lsp.validation.models import ValidationError, ValidationMode, ValidationResult


class MaidRunner:
    """Async wrapper for maid-runner library.

    This class provides an async interface to the maid-runner library,
    allowing validation of manifests and discovery of related manifests
    for source files.

    Attributes:
        timeout: Timeout in seconds for validation operations.
    """

    def __init__(
        self,
        timeout: float = 10.0,
    ) -> None:
        """Initialize MaidRunner.

        Args:
            timeout: Timeout in seconds for validation operations. Defaults to 10.0.
        """
        self.timeout = timeout

    async def validate(
        self,
        manifest_path: Path,
        mode: ValidationMode,
    ) -> ValidationResult:
        """Validate a manifest using the maid-runner library.

        Calls maid_runner.validate() in a thread to avoid blocking the event loop.

        Args:
            manifest_path: Path to the manifest file to validate.
            mode: Validation mode (behavioral or implementation).

        Returns:
            ValidationResult containing success status, errors, warnings, and metadata.

        Raises:
            asyncio.TimeoutError: If the validation operation times out.
        """
        result = await asyncio.wait_for(
            asyncio.to_thread(
                maid_validate,
                str(manifest_path),
                mode=MaidValidationMode(mode.value),
                use_chain=True,
            ),
            timeout=self.timeout,
        )

        output_data = result.to_dict()

        errors = [
            ValidationError(
                code=e["code"],
                message=e["message"],
                file=e.get("file"),
                line=e.get("line"),
                column=e.get("column"),
                severity=e.get("severity", "error"),
            )
            for e in output_data.get("errors", [])
        ]

        warnings = [
            ValidationError(
                code=w["code"],
                message=w["message"],
                file=w.get("file"),
                line=w.get("line"),
                column=w.get("column"),
                severity=w.get("severity", "warning"),
            )
            for w in output_data.get("warnings", [])
        ]

        return ValidationResult(
            success=output_data.get("success", False),
            errors=errors,
            warnings=warnings,
            metadata=output_data.get("metadata", {}),
        )

    async def find_manifests(self, file_path: Path) -> list[Path]:
        """Find manifests associated with a source file.

        Uses ManifestChain to discover manifest files related to the given source file.

        Args:
            file_path: Path to the source file.

        Returns:
            List of Path objects pointing to manifest files.

        Raises:
            asyncio.TimeoutError: If the operation times out.
        """

        def _find() -> list[str]:
            chain = ManifestChain(str(Path.cwd()))
            return [str(m) for m in chain.manifests_for_file(str(file_path))]

        result = await asyncio.wait_for(
            asyncio.to_thread(_find),
            timeout=self.timeout,
        )

        return [Path(p) for p in result]
