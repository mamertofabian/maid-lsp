"""Behavioral tests for Task 005: Validation Parser.

These tests verify that the validation parser correctly converts ValidationResult
objects to LSP Diagnostic objects, maps error codes to severities, and parses
error locations into LSP Range objects.
"""

from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

from maid_lsp.validation.models import ValidationError, ValidationResult
from maid_lsp.validation.parser import (
    map_error_code_to_severity,
    parse_error_location,
    validation_result_to_diagnostics,
)


class TestValidationResultToDiagnostics:
    """Test validation_result_to_diagnostics function."""

    def test_converts_errors_to_diagnostics(self) -> None:
        """Should convert ValidationResult with errors to list of Diagnostic."""
        error = ValidationError(
            code="MAID-001",
            message="Missing required field 'goal'",
            file="/path/to/manifest.json",
            line=1,
            column=1,
            severity="error",
        )
        result = ValidationResult(
            success=False,
            errors=[error],
            warnings=[],
            metadata={},
        )

        diagnostics = validation_result_to_diagnostics(result, "file:///path/to/manifest.json")

        assert isinstance(diagnostics, list)
        assert len(diagnostics) == 1
        assert isinstance(diagnostics[0], Diagnostic)
        assert diagnostics[0].message == "Missing required field 'goal'"

    def test_converts_warnings_to_diagnostics(self) -> None:
        """Should convert ValidationResult with warnings to list of Diagnostic."""
        warning = ValidationError(
            code="MAID-008",
            message="Deprecated field usage",
            file="/path/to/manifest.json",
            line=5,
            column=3,
            severity="warning",
        )
        result = ValidationResult(
            success=True,
            errors=[],
            warnings=[warning],
            metadata={},
        )

        diagnostics = validation_result_to_diagnostics(result, "file:///path/to/manifest.json")

        assert isinstance(diagnostics, list)
        assert len(diagnostics) == 1
        assert isinstance(diagnostics[0], Diagnostic)
        assert diagnostics[0].message == "Deprecated field usage"
        assert diagnostics[0].severity == DiagnosticSeverity.Warning

    def test_empty_result_returns_empty_list(self) -> None:
        """Should return empty list when ValidationResult has no errors or warnings."""
        result = ValidationResult(
            success=True,
            errors=[],
            warnings=[],
            metadata={},
        )

        diagnostics = validation_result_to_diagnostics(result, "file:///path/to/manifest.json")

        assert diagnostics == []
        assert len(diagnostics) == 0

    def test_diagnostics_have_correct_source(self) -> None:
        """Diagnostics should have source set to 'maid-lsp'."""
        error = ValidationError(
            code="MAID-002",
            message="Test error",
            file="/path/to/manifest.json",
            line=1,
            column=1,
            severity="error",
        )
        result = ValidationResult(
            success=False,
            errors=[error],
            warnings=[],
            metadata={},
        )

        diagnostics = validation_result_to_diagnostics(result, "file:///path/to/manifest.json")

        assert len(diagnostics) == 1
        assert diagnostics[0].source == "maid-lsp"

    def test_diagnostics_have_correct_code(self) -> None:
        """Diagnostics should have code set to MAID-XXX format."""
        error = ValidationError(
            code="MAID-003",
            message="Invalid task type",
            file="/path/to/manifest.json",
            line=2,
            column=5,
            severity="error",
        )
        result = ValidationResult(
            success=False,
            errors=[error],
            warnings=[],
            metadata={},
        )

        diagnostics = validation_result_to_diagnostics(result, "file:///path/to/manifest.json")

        assert len(diagnostics) == 1
        assert diagnostics[0].code == "MAID-003"

    def test_converts_multiple_errors(self) -> None:
        """Should convert multiple errors to multiple diagnostics."""
        errors = [
            ValidationError(
                code="MAID-001",
                message="First error",
                file="/path/to/manifest.json",
                line=1,
                column=1,
                severity="error",
            ),
            ValidationError(
                code="MAID-002",
                message="Second error",
                file="/path/to/manifest.json",
                line=5,
                column=10,
                severity="error",
            ),
        ]
        result = ValidationResult(
            success=False,
            errors=errors,
            warnings=[],
            metadata={},
        )

        diagnostics = validation_result_to_diagnostics(result, "file:///path/to/manifest.json")

        assert len(diagnostics) == 2
        assert diagnostics[0].code == "MAID-001"
        assert diagnostics[1].code == "MAID-002"

    def test_converts_errors_and_warnings_together(self) -> None:
        """Should convert both errors and warnings to diagnostics."""
        error = ValidationError(
            code="MAID-001",
            message="Error message",
            file="/path/to/manifest.json",
            line=1,
            column=1,
            severity="error",
        )
        warning = ValidationError(
            code="MAID-008",
            message="Warning message",
            file="/path/to/manifest.json",
            line=10,
            column=1,
            severity="warning",
        )
        result = ValidationResult(
            success=False,
            errors=[error],
            warnings=[warning],
            metadata={},
        )

        diagnostics = validation_result_to_diagnostics(result, "file:///path/to/manifest.json")

        assert len(diagnostics) == 2
        # Check that we have both error and warning diagnostics
        severities = [d.severity for d in diagnostics]
        assert DiagnosticSeverity.Error in severities
        assert DiagnosticSeverity.Warning in severities

    def test_diagnostics_have_correct_range(self) -> None:
        """Diagnostics should have Range based on error location."""
        error = ValidationError(
            code="MAID-004",
            message="Test error",
            file="/path/to/manifest.json",
            line=10,
            column=5,
            severity="error",
        )
        result = ValidationResult(
            success=False,
            errors=[error],
            warnings=[],
            metadata={},
        )

        diagnostics = validation_result_to_diagnostics(result, "file:///path/to/manifest.json")

        assert len(diagnostics) == 1
        assert isinstance(diagnostics[0].range, Range)
        # LSP uses 0-based line numbers, so line 10 becomes 9
        assert diagnostics[0].range.start.line == 9
        assert diagnostics[0].range.start.character == 4  # column 5 becomes 4


class TestMapErrorCodeToSeverity:
    """Test map_error_code_to_severity function."""

    def test_maid_001_returns_error(self) -> None:
        """MAID-001 should return Error severity."""
        severity = map_error_code_to_severity("MAID-001")
        assert severity == DiagnosticSeverity.Error

    def test_maid_002_returns_error(self) -> None:
        """MAID-002 should return Error severity."""
        severity = map_error_code_to_severity("MAID-002")
        assert severity == DiagnosticSeverity.Error

    def test_maid_003_returns_error(self) -> None:
        """MAID-003 should return Error severity."""
        severity = map_error_code_to_severity("MAID-003")
        assert severity == DiagnosticSeverity.Error

    def test_maid_004_returns_error(self) -> None:
        """MAID-004 should return Error severity."""
        severity = map_error_code_to_severity("MAID-004")
        assert severity == DiagnosticSeverity.Error

    def test_maid_005_returns_error(self) -> None:
        """MAID-005 should return Error severity."""
        severity = map_error_code_to_severity("MAID-005")
        assert severity == DiagnosticSeverity.Error

    def test_maid_006_returns_error(self) -> None:
        """MAID-006 should return Error severity."""
        severity = map_error_code_to_severity("MAID-006")
        assert severity == DiagnosticSeverity.Error

    def test_maid_007_returns_error(self) -> None:
        """MAID-007 should return Error severity."""
        severity = map_error_code_to_severity("MAID-007")
        assert severity == DiagnosticSeverity.Error

    def test_maid_008_returns_warning(self) -> None:
        """MAID-008 should return Warning severity."""
        severity = map_error_code_to_severity("MAID-008")
        assert severity == DiagnosticSeverity.Warning

    def test_unknown_code_defaults_to_error(self) -> None:
        """Unknown error codes should default to Error severity."""
        severity = map_error_code_to_severity("MAID-999")
        assert severity == DiagnosticSeverity.Error

    def test_unknown_format_defaults_to_error(self) -> None:
        """Non-MAID format codes should default to Error severity."""
        severity = map_error_code_to_severity("E001")
        assert severity == DiagnosticSeverity.Error

    def test_empty_code_defaults_to_error(self) -> None:
        """Empty code should default to Error severity."""
        severity = map_error_code_to_severity("")
        assert severity == DiagnosticSeverity.Error


class TestParseErrorLocation:
    """Test parse_error_location function."""

    def test_creates_range_from_line_and_column(self) -> None:
        """Should create Range from line and column info."""
        error = ValidationError(
            code="MAID-001",
            message="Test error",
            file="/path/to/manifest.json",
            line=10,
            column=5,
            severity="error",
        )

        range_obj = parse_error_location(error, "file:///path/to/manifest.json")

        assert isinstance(range_obj, Range)
        assert isinstance(range_obj.start, Position)
        assert isinstance(range_obj.end, Position)
        # LSP uses 0-based indices
        assert range_obj.start.line == 9
        assert range_obj.start.character == 4

    def test_handles_none_line_defaults_to_zero(self) -> None:
        """Should default to line 0 when line is None."""
        error = ValidationError(
            code="MAID-001",
            message="Test error",
            file="/path/to/manifest.json",
            line=None,
            column=5,
            severity="error",
        )

        range_obj = parse_error_location(error, "file:///path/to/manifest.json")

        assert range_obj.start.line == 0
        assert range_obj.end.line == 0

    def test_handles_none_column_defaults_to_zero(self) -> None:
        """Should default to column 0 when column is None."""
        error = ValidationError(
            code="MAID-001",
            message="Test error",
            file="/path/to/manifest.json",
            line=10,
            column=None,
            severity="error",
        )

        range_obj = parse_error_location(error, "file:///path/to/manifest.json")

        assert range_obj.start.character == 0
        assert range_obj.end.character == 0

    def test_handles_both_none_defaults_to_zero(self) -> None:
        """Should default to line 0, column 0 when both are None."""
        error = ValidationError(
            code="MAID-001",
            message="Test error",
            file="/path/to/manifest.json",
            line=None,
            column=None,
            severity="error",
        )

        range_obj = parse_error_location(error, "file:///path/to/manifest.json")

        assert range_obj.start.line == 0
        assert range_obj.start.character == 0
        assert range_obj.end.line == 0
        assert range_obj.end.character == 0

    def test_first_line_is_zero_indexed(self) -> None:
        """Line 1 in error should map to line 0 in LSP Range."""
        error = ValidationError(
            code="MAID-001",
            message="Test error",
            file="/path/to/manifest.json",
            line=1,
            column=1,
            severity="error",
        )

        range_obj = parse_error_location(error, "file:///path/to/manifest.json")

        assert range_obj.start.line == 0
        assert range_obj.start.character == 0

    def test_returns_range_with_start_and_end(self) -> None:
        """Should return Range with both start and end Position."""
        error = ValidationError(
            code="MAID-001",
            message="Test error",
            file="/path/to/manifest.json",
            line=5,
            column=10,
            severity="error",
        )

        range_obj = parse_error_location(error, "file:///path/to/manifest.json")

        assert hasattr(range_obj, "start")
        assert hasattr(range_obj, "end")
        assert isinstance(range_obj.start, Position)
        assert isinstance(range_obj.end, Position)

    def test_range_end_is_valid(self) -> None:
        """Range end should be at least at the start position."""
        error = ValidationError(
            code="MAID-001",
            message="Test error",
            file="/path/to/manifest.json",
            line=5,
            column=10,
            severity="error",
        )

        range_obj = parse_error_location(error, "file:///path/to/manifest.json")

        # End should be at or after start
        assert range_obj.end.line >= range_obj.start.line
        if range_obj.end.line == range_obj.start.line:
            assert range_obj.end.character >= range_obj.start.character
