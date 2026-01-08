"""Behavioral tests for Task 003: Validation Models.

These tests verify that the validation data models are properly defined
with all required attributes and correct types for use throughout the
validation layer.
"""

from enum import Enum

from maid_lsp.validation.models import ValidationError, ValidationMode, ValidationResult


class TestValidationError:
    """Test ValidationError data class."""

    def test_validation_error_instantiation(self) -> None:
        """ValidationError should be instantiable with required fields."""
        error = ValidationError(
            code="E001",
            message="Test error message",
            file="test.manifest.json",
            line=10,
            column=5,
            severity="error",
        )
        assert error is not None

    def test_validation_error_code_attribute(self) -> None:
        """ValidationError should have accessible code attribute."""
        error = ValidationError(
            code="E002",
            message="Another error",
            file="test.json",
            line=1,
            column=1,
            severity="error",
        )
        assert error.code == "E002"

    def test_validation_error_message_attribute(self) -> None:
        """ValidationError should have accessible message attribute."""
        error = ValidationError(
            code="E001",
            message="Expected message content",
            file="test.json",
            line=1,
            column=1,
            severity="error",
        )
        assert error.message == "Expected message content"

    def test_validation_error_file_attribute(self) -> None:
        """ValidationError should have accessible file attribute."""
        error = ValidationError(
            code="E001",
            message="Test",
            file="/path/to/manifest.json",
            line=1,
            column=1,
            severity="error",
        )
        assert error.file == "/path/to/manifest.json"

    def test_validation_error_line_attribute(self) -> None:
        """ValidationError should have accessible line attribute."""
        error = ValidationError(
            code="E001",
            message="Test",
            file="test.json",
            line=42,
            column=1,
            severity="error",
        )
        assert error.line == 42

    def test_validation_error_column_attribute(self) -> None:
        """ValidationError should have accessible column attribute."""
        error = ValidationError(
            code="E001",
            message="Test",
            file="test.json",
            line=1,
            column=15,
            severity="error",
        )
        assert error.column == 15

    def test_validation_error_severity_attribute(self) -> None:
        """ValidationError should have accessible severity attribute."""
        error = ValidationError(
            code="E001",
            message="Test",
            file="test.json",
            line=1,
            column=1,
            severity="warning",
        )
        assert error.severity == "warning"

    def test_validation_error_all_attributes_accessible(self) -> None:
        """All ValidationError attributes should be accessible together."""
        error = ValidationError(
            code="E999",
            message="Complete test",
            file="complete.json",
            line=100,
            column=50,
            severity="error",
        )
        assert error.code == "E999"
        assert error.message == "Complete test"
        assert error.file == "complete.json"
        assert error.line == 100
        assert error.column == 50
        assert error.severity == "error"


class TestValidationResult:
    """Test ValidationResult data class."""

    def test_validation_result_instantiation(self) -> None:
        """ValidationResult should be instantiable with required fields."""
        result = ValidationResult(
            success=True,
            errors=[],
            warnings=[],
            metadata={},
        )
        assert result is not None

    def test_validation_result_success_attribute(self) -> None:
        """ValidationResult should have accessible success attribute."""
        result = ValidationResult(
            success=True,
            errors=[],
            warnings=[],
            metadata={},
        )
        assert result.success is True

        result_failed = ValidationResult(
            success=False,
            errors=[],
            warnings=[],
            metadata={},
        )
        assert result_failed.success is False

    def test_validation_result_errors_attribute(self) -> None:
        """ValidationResult should have accessible errors attribute."""
        error = ValidationError(
            code="E001",
            message="Test error",
            file="test.json",
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
        assert result.errors == [error]
        assert len(result.errors) == 1
        assert result.errors[0].code == "E001"

    def test_validation_result_warnings_attribute(self) -> None:
        """ValidationResult should have accessible warnings attribute."""
        warning = ValidationError(
            code="W001",
            message="Test warning",
            file="test.json",
            line=5,
            column=1,
            severity="warning",
        )
        result = ValidationResult(
            success=True,
            errors=[],
            warnings=[warning],
            metadata={},
        )
        assert result.warnings == [warning]
        assert len(result.warnings) == 1
        assert result.warnings[0].code == "W001"

    def test_validation_result_metadata_attribute(self) -> None:
        """ValidationResult should have accessible metadata attribute."""
        result = ValidationResult(
            success=True,
            errors=[],
            warnings=[],
            metadata={"duration_ms": 150, "validator_version": "1.0.0"},
        )
        assert result.metadata == {"duration_ms": 150, "validator_version": "1.0.0"}
        assert result.metadata["duration_ms"] == 150

    def test_validation_result_with_multiple_errors(self) -> None:
        """ValidationResult should handle multiple errors."""
        errors = [
            ValidationError(
                code="E001",
                message="First error",
                file="test.json",
                line=1,
                column=1,
                severity="error",
            ),
            ValidationError(
                code="E002",
                message="Second error",
                file="test.json",
                line=10,
                column=5,
                severity="error",
            ),
        ]
        result = ValidationResult(
            success=False,
            errors=errors,
            warnings=[],
            metadata={},
        )
        assert len(result.errors) == 2
        assert result.errors[0].code == "E001"
        assert result.errors[1].code == "E002"

    def test_validation_result_empty_lists(self) -> None:
        """ValidationResult should accept empty lists for errors and warnings."""
        result = ValidationResult(
            success=True,
            errors=[],
            warnings=[],
            metadata={},
        )
        assert result.errors == []
        assert result.warnings == []
        assert len(result.errors) == 0
        assert len(result.warnings) == 0


class TestValidationMode:
    """Test ValidationMode enum."""

    def test_validation_mode_is_enum(self) -> None:
        """ValidationMode should be an Enum type."""
        assert issubclass(ValidationMode, Enum)

    def test_validation_mode_has_behavioral(self) -> None:
        """ValidationMode should have BEHAVIORAL value."""
        assert hasattr(ValidationMode, "BEHAVIORAL")
        mode = ValidationMode.BEHAVIORAL
        assert mode is not None

    def test_validation_mode_has_implementation(self) -> None:
        """ValidationMode should have IMPLEMENTATION value."""
        assert hasattr(ValidationMode, "IMPLEMENTATION")
        mode = ValidationMode.IMPLEMENTATION
        assert mode is not None

    def test_validation_mode_behavioral_value(self) -> None:
        """ValidationMode.BEHAVIORAL should have a consistent value."""
        mode = ValidationMode.BEHAVIORAL
        assert mode.name == "BEHAVIORAL"

    def test_validation_mode_implementation_value(self) -> None:
        """ValidationMode.IMPLEMENTATION should have a consistent value."""
        mode = ValidationMode.IMPLEMENTATION
        assert mode.name == "IMPLEMENTATION"

    def test_validation_mode_values_are_different(self) -> None:
        """BEHAVIORAL and IMPLEMENTATION should be distinct enum values."""
        assert ValidationMode.BEHAVIORAL != ValidationMode.IMPLEMENTATION

    def test_validation_mode_iteration(self) -> None:
        """ValidationMode should have at least BEHAVIORAL and IMPLEMENTATION."""
        modes = list(ValidationMode)
        mode_names = [m.name for m in modes]
        assert "BEHAVIORAL" in mode_names
        assert "IMPLEMENTATION" in mode_names
        assert len(modes) >= 2
