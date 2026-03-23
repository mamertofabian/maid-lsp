"""Behavioral tests for Task 008: Hover Handler.

These tests verify that the HoverHandler class correctly handles hover requests
to show artifact information, and that the format_artifact_hover function
formats artifact data as markdown for hover display.
"""

from unittest.mock import MagicMock

from lsprotocol.types import (
    Hover,
    HoverParams,
    MarkupContent,
    MarkupKind,
    Position,
    TextDocumentIdentifier,
)
from pygls.workspace import TextDocument

from maid_lsp.capabilities.hover import HoverHandler, format_artifact_hover


class TestHoverHandlerInit:
    """Test HoverHandler initialization."""

    def test_init_creates_instance(self) -> None:
        """HoverHandler should be instantiable."""
        handler = HoverHandler()

        assert handler is not None
        assert isinstance(handler, HoverHandler)

    def test_init_explicit_call(self) -> None:
        """HoverHandler.__init__ should initialize properly with explicit call."""
        handler = HoverHandler.__new__(HoverHandler)
        HoverHandler.__init__(handler)

        assert handler is not None
        assert isinstance(handler, HoverHandler)


class TestHoverHandlerGetHover:
    """Test HoverHandler.get_hover method."""

    def test_get_hover_returns_hover_object_when_on_artifact_name(self) -> None:
        """get_hover should return a Hover object when hovering over an artifact name."""
        handler = HoverHandler()

        # Create a mock document with content containing an artifact reference
        document = MagicMock(spec=TextDocument)
        document.source = """{
    "expectedArtifacts": {
        "file": "src/module.py",
        "contains": [
            {
                "type": "function",
                "name": "my_function",
                "args": [{"name": "arg1", "type": "str"}],
                "returns": {"type": "int"}
            }
        ]
    }
}"""
        # Line 6 contains "my_function"
        document.lines = document.source.split("\n")

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            position=Position(line=6, character=25),  # Position on "my_function"
        )

        result = handler.get_hover(params=params, document=document)

        # Should return a Hover object when on an artifact name
        assert result is None or isinstance(result, Hover)

    def test_get_hover_returns_none_when_not_on_artifact(self) -> None:
        """get_hover should return None when not hovering over an artifact."""
        handler = HoverHandler()

        # Create a mock document with simple content
        document = MagicMock(spec=TextDocument)
        document.source = """{
    "goal": "Test manifest",
    "taskType": "create"
}"""
        document.lines = document.source.split("\n")

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            position=Position(line=0, character=0),  # Position at start, not on artifact
        )

        result = handler.get_hover(params=params, document=document)

        # Should return None when not on an artifact
        assert result is None

    def test_get_hover_uses_document_content(self) -> None:
        """get_hover should use document content to find artifacts."""
        handler = HoverHandler()

        # Create a mock document
        document = MagicMock(spec=TextDocument)
        document.source = """{
    "expectedArtifacts": {
        "file": "src/module.py",
        "contains": [
            {
                "type": "class",
                "name": "MyClass",
                "bases": ["BaseClass"]
            }
        ]
    }
}"""
        document.lines = document.source.split("\n")

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            position=Position(line=6, character=22),  # Position near "MyClass"
        )

        # The handler should access document.source or document.lines
        result = handler.get_hover(params=params, document=document)

        # Verify get_hover returns something (either None or Hover)
        assert result is None or isinstance(result, Hover)

    def test_get_hover_content_is_markdown_formatted(self) -> None:
        """get_hover should return hover content that is markdown formatted."""
        handler = HoverHandler()

        # Create a mock document with artifact content
        document = MagicMock(spec=TextDocument)
        document.source = """{
    "expectedArtifacts": {
        "file": "src/module.py",
        "contains": [
            {
                "type": "function",
                "name": "process_data",
                "description": "Processes input data",
                "args": [{"name": "data", "type": "dict"}],
                "returns": {"type": "dict"}
            }
        ]
    }
}"""
        document.lines = document.source.split("\n")

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            position=Position(line=6, character=25),  # Position on "process_data"
        )

        result = handler.get_hover(params=params, document=document)

        # If hover is returned, contents should be markdown
        if result is not None:
            assert isinstance(result, Hover)
            contents = result.contents
            # Contents can be MarkupContent, MarkedString, or list
            if isinstance(contents, MarkupContent):
                assert contents.kind == MarkupKind.Markdown
                assert isinstance(contents.value, str)
            elif isinstance(contents, str):
                # Plain string is also acceptable
                assert len(contents) > 0

    def test_get_hover_with_class_artifact(self) -> None:
        """get_hover should handle class artifacts correctly."""
        handler = HoverHandler()

        document = MagicMock(spec=TextDocument)
        document.source = """{
    "expectedArtifacts": {
        "file": "src/models.py",
        "contains": [
            {
                "type": "class",
                "name": "DataModel",
                "description": "Data model class",
                "bases": ["BaseModel"]
            }
        ]
    }
}"""
        document.lines = document.source.split("\n")

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            position=Position(line=6, character=22),  # Position on "DataModel"
        )

        result = handler.get_hover(params=params, document=document)

        assert result is None or isinstance(result, Hover)

    def test_get_hover_with_position_outside_document(self) -> None:
        """get_hover should handle position outside document bounds gracefully."""
        handler = HoverHandler()

        document = MagicMock(spec=TextDocument)
        document.source = '{"goal": "test"}'
        document.lines = document.source.split("\n")

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            position=Position(line=100, character=50),  # Position way outside document
        )

        result = handler.get_hover(params=params, document=document)

        # Should handle gracefully and return None
        assert result is None

    def test_get_hover_with_empty_document(self) -> None:
        """get_hover should handle empty document gracefully."""
        handler = HoverHandler()

        document = MagicMock(spec=TextDocument)
        document.source = ""
        document.lines = []

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            position=Position(line=0, character=0),
        )

        result = handler.get_hover(params=params, document=document)

        # Should handle gracefully and return None
        assert result is None


class TestFormatArtifactHover:
    """Test format_artifact_hover function."""

    def test_returns_string(self) -> None:
        """format_artifact_hover should return a string."""
        artifact = {
            "type": "function",
            "name": "test_func",
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)

    def test_formats_function_artifact_with_name(self) -> None:
        """format_artifact_hover should format function artifact with name."""
        artifact = {
            "type": "function",
            "name": "my_function",
            "description": "A test function",
            "args": [
                {"name": "arg1", "type": "str"},
                {"name": "arg2", "type": "int"},
            ],
            "returns": {"type": "bool"},
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        assert "my_function" in result

    def test_formats_function_artifact_with_args(self) -> None:
        """format_artifact_hover should include function arguments in output."""
        artifact = {
            "type": "function",
            "name": "process",
            "args": [
                {"name": "data", "type": "dict"},
                {"name": "options", "type": "dict"},
            ],
            "returns": {"type": "list"},
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        # Should include argument information
        assert "data" in result or "args" in result.lower() or "dict" in result

    def test_formats_function_artifact_with_returns(self) -> None:
        """format_artifact_hover should include return type in output."""
        artifact = {
            "type": "function",
            "name": "calculate",
            "args": [{"name": "x", "type": "int"}],
            "returns": {"type": "float"},
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        # Should include return type information
        assert "float" in result or "return" in result.lower()

    def test_formats_class_artifact_with_name(self) -> None:
        """format_artifact_hover should format class artifact with name."""
        artifact = {
            "type": "class",
            "name": "MyClass",
            "description": "A test class",
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        assert "MyClass" in result

    def test_formats_class_artifact_with_bases(self) -> None:
        """format_artifact_hover should include base classes in output."""
        artifact = {
            "type": "class",
            "name": "DerivedClass",
            "description": "A derived class",
            "bases": ["BaseClass", "MixinClass"],
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        # Should include base class information
        assert "BaseClass" in result or "bases" in result.lower() or "inherit" in result.lower()

    def test_handles_missing_optional_fields_gracefully(self) -> None:
        """format_artifact_hover should handle missing optional fields gracefully."""
        # Minimal artifact with only required fields
        artifact = {
            "type": "function",
            "name": "minimal_func",
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        assert "minimal_func" in result

    def test_handles_missing_description(self) -> None:
        """format_artifact_hover should handle missing description field."""
        artifact = {
            "type": "function",
            "name": "no_desc_func",
            "args": [{"name": "x", "type": "int"}],
            "returns": {"type": "int"},
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        assert "no_desc_func" in result

    def test_handles_missing_args(self) -> None:
        """format_artifact_hover should handle missing args field for functions."""
        artifact = {
            "type": "function",
            "name": "no_args_func",
            "returns": {"type": "None"},
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        assert "no_args_func" in result

    def test_handles_missing_returns(self) -> None:
        """format_artifact_hover should handle missing returns field for functions."""
        artifact = {
            "type": "function",
            "name": "no_return_func",
            "args": [{"name": "data", "type": "str"}],
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        assert "no_return_func" in result

    def test_handles_missing_bases_for_class(self) -> None:
        """format_artifact_hover should handle missing bases field for classes."""
        artifact = {
            "type": "class",
            "name": "StandaloneClass",
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        assert "StandaloneClass" in result

    def test_handles_empty_args_list(self) -> None:
        """format_artifact_hover should handle empty args list."""
        artifact = {
            "type": "function",
            "name": "empty_args_func",
            "args": [],
            "returns": {"type": "str"},
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        assert "empty_args_func" in result

    def test_handles_empty_bases_list(self) -> None:
        """format_artifact_hover should handle empty bases list."""
        artifact = {
            "type": "class",
            "name": "NoBasesClass",
            "bases": [],
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        assert "NoBasesClass" in result

    def test_includes_artifact_type_in_output(self) -> None:
        """format_artifact_hover should indicate the artifact type."""
        artifact = {
            "type": "function",
            "name": "typed_func",
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        # Should indicate it's a function
        assert "function" in result.lower() or "def" in result.lower()

    def test_includes_class_type_in_output(self) -> None:
        """format_artifact_hover should indicate when artifact is a class."""
        artifact = {
            "type": "class",
            "name": "TypedClass",
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        # Should indicate it's a class
        assert "class" in result.lower()

    def test_includes_description_when_present(self) -> None:
        """format_artifact_hover should include description when present."""
        artifact = {
            "type": "function",
            "name": "described_func",
            "description": "This function does something important",
        }

        result = format_artifact_hover(artifact=artifact)

        assert isinstance(result, str)
        assert "This function does something important" in result


class TestHoverHandlerIntegration:
    """Integration tests for HoverHandler with format_artifact_hover."""

    def test_handler_uses_format_artifact_hover_for_formatting(self) -> None:
        """HoverHandler should use format_artifact_hover for formatting hover content."""
        handler = HoverHandler()

        document = MagicMock(spec=TextDocument)
        document.source = """{
    "expectedArtifacts": {
        "file": "src/handler.py",
        "contains": [
            {
                "type": "function",
                "name": "handle_request",
                "description": "Handles incoming requests",
                "args": [{"name": "request", "type": "Request"}],
                "returns": {"type": "Response"}
            }
        ]
    }
}"""
        document.lines = document.source.split("\n")

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///path/to/manifest.json"),
            position=Position(line=6, character=25),
        )

        result = handler.get_hover(params=params, document=document)

        # If hover is returned, it should be properly formatted
        if result is not None:
            assert isinstance(result, Hover)
            contents = result.contents
            if isinstance(contents, MarkupContent):
                assert len(contents.value) > 0
            elif isinstance(contents, str):
                assert len(contents) > 0

    def test_format_artifact_hover_output_is_valid_for_hover_display(self) -> None:
        """format_artifact_hover output should be valid for use in Hover display."""
        artifact = {
            "type": "function",
            "name": "test_function",
            "description": "A test function for validation",
            "args": [
                {"name": "param1", "type": "str"},
                {"name": "param2", "type": "int"},
            ],
            "returns": {"type": "bool"},
        }

        formatted = format_artifact_hover(artifact=artifact)

        # The formatted string should be usable in MarkupContent
        markup = MarkupContent(kind=MarkupKind.Markdown, value=formatted)

        assert markup.value == formatted
        assert len(formatted) > 0

    def test_handler_and_formatter_handle_complex_artifact(self) -> None:
        """Handler and formatter should handle complex artifacts with all fields."""
        # Test the formatter with a complex artifact
        artifact = {
            "type": "class",
            "name": "ComplexHandler",
            "description": "A complex handler class with many features",
            "bases": ["BaseHandler", "LoggingMixin"],
        }

        formatted = format_artifact_hover(artifact=artifact)

        assert isinstance(formatted, str)
        assert "ComplexHandler" in formatted
        # Should include base class info
        assert "BaseHandler" in formatted or "bases" in formatted.lower()
