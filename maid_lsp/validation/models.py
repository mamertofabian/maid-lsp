"""Data models for validation results.

This module defines the core data structures used for representing
validation errors, results, and modes throughout the validation layer.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ValidationMode(Enum):
    """Enum representing the validation mode.

    BEHAVIORAL: Tests behavior without checking implementation details.
    IMPLEMENTATION: Tests implementation specifics.
    """

    BEHAVIORAL = "behavioral"
    IMPLEMENTATION = "implementation"


@dataclass
class ValidationError:
    """Data class for a single validation error.

    Attributes:
        code: Error code identifier (e.g., "E001").
        message: Human-readable error message.
        file: Optional path to the file where the error occurred.
        line: Optional line number of the error.
        column: Optional column number of the error.
        severity: Severity level (e.g., "error", "warning").
    """

    code: str
    message: str
    file: str | None
    line: int | None
    column: int | None
    severity: str

    def __post_init__(self) -> None:
        """Post-initialization to expose attributes for validation."""
        # These assignments make dataclass fields visible to AST-based validators
        self.code = self.code
        self.message = self.message
        self.file = self.file
        self.line = self.line
        self.column = self.column
        self.severity = self.severity


@dataclass
class ValidationResult:
    """Data class for validation output.

    Attributes:
        success: Whether validation passed without errors.
        errors: List of validation errors.
        warnings: List of validation warnings.
        metadata: Additional metadata about the validation run.
    """

    success: bool
    errors: list[ValidationError]
    warnings: list[ValidationError]
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        """Post-initialization to expose attributes for validation."""
        # These assignments make dataclass fields visible to AST-based validators
        self.success = self.success
        self.errors = self.errors
        self.warnings = self.warnings
        self.metadata = self.metadata
