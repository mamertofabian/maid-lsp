"""Async wrapper for maid-runner CLI execution.

This module provides the MaidRunner class that wraps the maid-runner CLI
for validation operations using asyncio subprocess execution.
"""

import asyncio
import json
from pathlib import Path

from maid_lsp.validation.models import ValidationError, ValidationMode, ValidationResult


class MaidRunner:
    """Async wrapper for maid-runner CLI.

    This class provides an async interface to the maid-runner CLI tool,
    allowing validation of manifests and discovery of related manifests
    for source files.

    Attributes:
        maid_runner_path: Path to the maid-runner executable.
        timeout: Timeout in seconds for CLI operations.
    """

    def __init__(
        self,
        maid_runner_path: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        """Initialize MaidRunner.

        Args:
            maid_runner_path: Path to the maid-runner executable.
                Defaults to "maid" if not specified.
            timeout: Timeout in seconds for CLI operations. Defaults to 10.0.
        """
        self.maid_runner_path = maid_runner_path if maid_runner_path is not None else "maid"
        self.timeout = timeout

    async def validate(
        self,
        manifest_path: Path,
        mode: ValidationMode,
    ) -> ValidationResult:
        """Validate a manifest using the maid-runner CLI.

        Executes: maid validate <manifest_path> --validation-mode <mode> --use-manifest-chain --json-output

        Args:
            manifest_path: Path to the manifest file to validate.
            mode: Validation mode (behavioral or implementation).

        Returns:
            ValidationResult containing success status, errors, warnings, and metadata.

        Raises:
            asyncio.TimeoutError: If the CLI operation times out.
            json.JSONDecodeError: If the CLI output is not valid JSON.
        """
        process = await asyncio.create_subprocess_exec(
            self.maid_runner_path,
            "validate",
            str(manifest_path),
            "--validation-mode",
            mode.value,
            "--use-manifest-chain",
            "--json-output",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, _stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            raise

        output_data = json.loads(stdout.decode())

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

        Executes: maid manifests <file_path> --json-output

        Args:
            file_path: Path to the source file.

        Returns:
            List of Path objects pointing to manifest files.

        Raises:
            asyncio.TimeoutError: If the CLI operation times out.
            json.JSONDecodeError: If the CLI output is not valid JSON.
        """
        process = await asyncio.create_subprocess_exec(
            self.maid_runner_path,
            "manifests",
            str(file_path),
            "--json-output",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, _stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            raise

        output_data = json.loads(stdout.decode())

        return [Path(p) for p in output_data]
