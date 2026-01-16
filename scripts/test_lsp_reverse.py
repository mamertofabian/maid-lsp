#!/usr/bin/env python3
"""Test reverse navigation: from source files to manifests.

This script tests go-to-definition and find-references when starting
from a source file (e.g., __init__.py) to navigate to manifests.
"""

import asyncio
import sys
from pathlib import Path

from maid_lsp.server import create_server
from lsprotocol.types import DefinitionParams, Position, ReferenceParams, TextDocumentIdentifier
from pygls.workspace import TextDocument


async def test_reverse_navigation(source_file: Path) -> None:
    """Test navigation from source file to manifest."""
    server = create_server()
    uri = f"file://{source_file.absolute()}"

    print(f"Testing reverse navigation from: {source_file}")
    print(f"URI: {uri}\n")

    # Read source file content
    content = source_file.read_text()
    doc = TextDocument(uri, content, language_id="python")

    # Find artifact names in the source file
    # For __init__.py, we know __version__ and __all__ are there
    lines = content.splitlines()
    artifact_positions = []
    
    # Look for __version__ and __all__
    for i, line in enumerate(lines):
        if "__version__" in line:
            char_pos = line.find("__version__")
            if char_pos != -1:
                artifact_positions.append((i, char_pos, "__version__"))
        if "__all__" in line:
            char_pos = line.find("__all__")
            if char_pos != -1:
                artifact_positions.append((i, char_pos, "__all__"))

    if not artifact_positions:
        print("⚠️  No artifact positions found in source file")
        return

    # Test go-to-definition (source → manifest)
    print("1. Testing go-to-definition (source → manifest)...")
    def_found = False
    for line_num, char_pos, artifact_name in artifact_positions[:1]:  # Test first artifact
        def_params = DefinitionParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=line_num, character=char_pos),
        )
        try:
            def_result = await server.definition_handler.get_definition_async(def_params, doc)
            if def_result:
                def_found = True
                if isinstance(def_result, list):
                    print(f"   ✅ Definition for '{artifact_name}' (line {line_num + 1}): Found {len(def_result)} location(s)")
                    for loc in def_result[:3]:
                        file_path = Path(loc.uri.replace("file://", ""))
                        print(f"     - {file_path.name}:{loc.range.start.line + 1}")
                else:
                    file_path = Path(def_result.uri.replace("file://", ""))
                    print(f"   ✅ Definition for '{artifact_name}' (line {line_num + 1}): {file_path.name}:{def_result.range.start.line + 1}")
                break
            else:
                print(f"   ⚠️  No definition found for '{artifact_name}'")
        except Exception as e:
            import traceback
            print(f"   ⚠️  Definition test error on '{artifact_name}': {e}")
            traceback.print_exc()
    
    if not def_found:
        print(f"   ⚠️  No definition found (tested {len(artifact_positions)} artifact positions)")

    # Test find-references (source → manifest + test files)
    print("\n2. Testing find-references (source → manifest + validationCommand)...")
    ref_found = False
    for line_num, char_pos, artifact_name in artifact_positions[:1]:  # Test first artifact
        ref_params = ReferenceParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=line_num, character=char_pos),
            context={"includeDeclaration": True},
        )
        try:
            ref_result = await server.references_handler.get_references(ref_params, doc)
            if ref_result:
                ref_found = True
                print(f"   ✅ References for '{artifact_name}' (line {line_num + 1}): Found {len(ref_result)} reference(s)")
                
                # Group by file type
                manifests = []
                tests = []
                sources = []
                
                for ref in ref_result:
                    file_path = Path(ref.uri.replace("file://", ""))
                    if file_path.name.endswith(".manifest.json"):
                        manifests.append((file_path, ref.range.start.line + 1))
                    elif "test" in file_path.name.lower():
                        tests.append((file_path, ref.range.start.line + 1))
                    else:
                        sources.append((file_path, ref.range.start.line + 1))
                
                if manifests:
                    print(f"     📄 In manifests ({len(manifests)}):")
                    for file_path, line in manifests[:3]:
                        print(f"       - {file_path.name}:{line}")
                
                if tests:
                    print(f"     🧪 In test files ({len(tests)}):")
                    for file_path, line in tests[:3]:
                        print(f"       - {file_path.name}:{line}")
                
                if sources:
                    print(f"     📝 In source files ({len(sources)}):")
                    for file_path, line in sources[:3]:
                        print(f"       - {file_path.name}:{line}")
                
                break
        except Exception as e:
            print(f"   ⚠️  References test error on '{artifact_name}': {e}")
    
    if not ref_found:
        print(f"   ⚠️  No references found (tested {len(artifact_positions)} artifact positions)")

    print("\n✅ Reverse navigation testing complete!")
    print("\n📊 Summary:")
    print(f"   - Go-to-Definition (source → manifest): {'✅ Working' if def_found else '⚠️  Not found'}")
    print(f"   - Find-References (source → manifest + tests): {'✅ Working' if ref_found else '⚠️  Not found'}")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_lsp_reverse.py <source-file>")
        print("\nExample:")
        print("  python scripts/test_lsp_reverse.py maid_lsp/__init__.py")
        sys.exit(1)

    source_file = Path(sys.argv[1])
    if not source_file.exists():
        print(f"Error: File not found: {source_file}")
        sys.exit(1)

    asyncio.run(test_reverse_navigation(source_file))


if __name__ == "__main__":
    main()
