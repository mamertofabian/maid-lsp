"""Parser for converting validation results to LSP diagnostics.

This module provides functions for converting ValidationResult objects from
maid-runner into LSP Diagnostic objects that can be sent to editors.
"""

from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

from maid_lsp.validation.models import ValidationError, ValidationResult


def validation_result_to_diagnostics(
    result: ValidationResult, default_uri: str
) -> list[Diagnostic]:
    """Converts ValidationResult to list of LSP Diagnostic objects.

    Takes a ValidationResult from maid-runner and converts all errors and
    warnings into LSP Diagnostic objects that can be published to the editor.

    Args:
        result: ValidationResult containing errors and warnings from validation.
        default_uri: Default document URI to use for diagnostics.

    Returns:
        List of Diagnostic objects representing all errors and warnings.
    """
    diagnostics: list[Diagnostic] = []

    # Process errors
    for error in result.errors:
        diagnostic = _create_diagnostic(error, default_uri)
        diagnostics.append(diagnostic)

    # Process warnings
    for warning in result.warnings:
        diagnostic = _create_diagnostic(warning, default_uri)
        diagnostics.append(diagnostic)

    return diagnostics


def map_error_code_to_severity(code: str) -> DiagnosticSeverity:
    """Maps MAID error codes to LSP DiagnosticSeverity.

    MAID-001 through MAID-007 are errors, MAID-008 is a warning.
    Unknown codes default to Error severity.

    Args:
        code: MAID error code string (e.g., "MAID-001").

    Returns:
        DiagnosticSeverity.Error for MAID-001 through MAID-007 and unknown codes.
        DiagnosticSeverity.Warning for MAID-008.
    """
    warning_codes = {"MAID-008"}

    if code in warning_codes:
        return DiagnosticSeverity.Warning

    return DiagnosticSeverity.Error


def parse_error_location(error: ValidationError, document_uri: str) -> Range:  # noqa: ARG001
    """Parses error location to LSP Range.

    Converts line and column from ValidationError (1-based) to LSP Range
    (0-based). Defaults to 0 if line or column is None.

    Args:
        error: ValidationError containing location information.
        document_uri: Document URI for the error location.

    Returns:
        Range object representing the error location.
    """
    # Convert 1-based line/column to 0-based, defaulting to 0 if None
    line = (error.line - 1) if error.line is not None else 0
    character = (error.column - 1) if error.column is not None else 0

    # Ensure non-negative values
    line = max(0, line)
    character = max(0, character)

    start = Position(line=line, character=character)
    end = Position(line=line, character=character)

    return Range(start=start, end=end)


def _create_diagnostic(error: ValidationError, default_uri: str) -> Diagnostic:
    """Creates a Diagnostic object from a ValidationError.

    Args:
        error: ValidationError to convert.
        default_uri: Default document URI for the diagnostic.

    Returns:
        Diagnostic object representing the validation error.
    """
    return Diagnostic(
        range=parse_error_location(error, default_uri),
        message=error.message,
        severity=map_error_code_to_severity(error.code),
        source="maid-lsp",
        code=error.code,
    )
