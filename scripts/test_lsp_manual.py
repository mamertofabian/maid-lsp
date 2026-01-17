#!/usr/bin/env python3
"""Manual LSP testing script.

This script allows you to interactively test the LSP server by sending
LSP protocol messages and seeing responses.

Usage:
    python scripts/test_lsp_manual.py <manifest-file>
"""

import asyncio
import json
import sys
from pathlib import Path

from maid_lsp.server import create_server


async def test_manifest(manifest_path: Path) -> None:
    """Test LSP server with a manifest file."""
    server = create_server()
    uri = f"file://{manifest_path.absolute()}"

    print(f"Testing manifest: {manifest_path}")
    print(f"URI: {uri}\n")

    # Read manifest content
    content = manifest_path.read_text()

    # Capture published diagnostics
    captured_diagnostics = []

    # Override publish_diagnostics to capture diagnostics
    def capture_publish(params):
        captured_diagnostics.append(params)
        # Don't call original since server isn't fully initialized

    server.text_document_publish_diagnostics = capture_publish

    # Simulate document open
    print("1. Testing validation...")

    # Trigger validation directly
    await server.diagnostics_handler.validate_and_publish(server, uri)

    # Wait for validation (with debouncing)
    print("   Waiting for validation (with debouncing)...")
    await asyncio.sleep(0.6)

    # Check captured diagnostics
    if captured_diagnostics:
        latest = captured_diagnostics[-1]
        diags = latest.diagnostics
        print(f"   ✅ Diagnostics published: {len(diags)}")
        for diag in diags[:5]:  # Show first 5
            print(f"   - {diag.code}: {diag.message}")
            if diag.range:
                print(
                    f"     At line {diag.range.start.line + 1}, col {diag.range.start.character + 1}"
                )
    else:
        print("   ⚠️  No diagnostics published (file may be valid or validation not triggered)")

    # Parse manifest to find artifact positions
    try:
        manifest_data = json.loads(content)
        expected_artifacts = manifest_data.get("expectedArtifacts", {})
        artifacts = expected_artifacts.get("contains", [])
    except json.JSONDecodeError:
        artifacts = []

    # Find artifact names and their positions in the file
    lines = content.splitlines()
    artifact_positions = []
    for i, line in enumerate(lines):
        # Look for artifact names (like "__version__", "__all__")
        for artifact in artifacts:
            if isinstance(artifact, dict):
                artifact_name = artifact.get("name")
                if artifact_name and artifact_name in line:
                    # Find the character position of the artifact name
                    char_pos = line.find(f'"{artifact_name}"')
                    if char_pos == -1:
                        char_pos = line.find(f"'{artifact_name}'")
                    if char_pos != -1:
                        # Position is inside the quotes, adjust to the name itself
                        artifact_positions.append((i, char_pos + 1, artifact_name))
                        break

    # Test hover on artifact names
    print("\n2. Testing hover on artifact names...")
    from lsprotocol.types import HoverParams, Position, TextDocumentIdentifier
    from pygls.workspace import TextDocument

    doc = TextDocument(uri, content, language_id="json")
    hover_found = False
    for line_num, char_pos, artifact_name in artifact_positions[:2]:  # Test first 2 artifacts
        hover_params = HoverParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=line_num, character=char_pos),
        )
        try:
            hover_result = server.hover_handler.get_hover(hover_params, doc)
            if hover_result and hover_result.contents:
                hover_found = True
                print(f"   ✅ Hover on '{artifact_name}' (line {line_num + 1}): Found info")
                if hasattr(hover_result.contents, "value"):
                    preview = hover_result.contents.value[:80]
                elif isinstance(hover_result.contents, str):
                    preview = hover_result.contents[:80]
                else:
                    preview = str(hover_result.contents)[:80]
                print(f"     Preview: {preview}...")
                break
        except Exception as e:
            print(f"   ⚠️  Hover test error on '{artifact_name}': {e}")

    if not hover_found and artifact_positions:
        print(f"   ⚠️  No hover info found (tested {len(artifact_positions)} artifact positions)")

    # Test definition on artifact names
    print("\n3. Testing go-to-definition on artifact names...")
    from lsprotocol.types import DefinitionParams

    def_found = False
    for line_num, char_pos, artifact_name in artifact_positions[:2]:  # Test first 2 artifacts
        def_params = DefinitionParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=line_num, character=char_pos),
        )
        try:
            def_result = await server.definition_handler.get_definition_async(def_params, doc)
            if def_result:
                def_found = True
                if isinstance(def_result, list):
                    print(
                        f"   ✅ Definition for '{artifact_name}' (line {line_num + 1}): Found {len(def_result)} location(s)"
                    )
                    for loc in def_result[:3]:
                        file_path = Path(loc.uri.replace("file://", ""))
                        print(f"     - {file_path.name}:{loc.range.start.line + 1}")
                else:
                    file_path = Path(def_result.uri.replace("file://", ""))
                    print(
                        f"   ✅ Definition for '{artifact_name}' (line {line_num + 1}): {file_path.name}:{def_result.range.start.line + 1}"
                    )
                break
        except Exception as e:
            print(f"   ⚠️  Definition test error on '{artifact_name}': {e}")

    if not def_found and artifact_positions:
        print(f"   ⚠️  No definition found (tested {len(artifact_positions)} artifact positions)")

    # Test references on artifact names
    print("\n4. Testing find-references on artifact names...")
    from lsprotocol.types import ReferenceParams

    ref_found = False
    for line_num, char_pos, artifact_name in artifact_positions[:2]:  # Test first 2 artifacts
        ref_params = ReferenceParams(
            text_document=TextDocumentIdentifier(uri=uri),
            position=Position(line=line_num, character=char_pos),
            context={"includeDeclaration": True},
        )
        try:
            ref_result = await server.references_handler.get_references(ref_params, doc)
            if ref_result:
                ref_found = True
                print(
                    f"   ✅ References for '{artifact_name}' (line {line_num + 1}): Found {len(ref_result)} reference(s)"
                )
                for ref in ref_result[:5]:  # Show first 5
                    file_path = Path(ref.uri.replace("file://", ""))
                    print(f"     - {file_path.name}:{ref.range.start.line + 1}")
                break
        except Exception as e:
            print(f"   ⚠️  References test error on '{artifact_name}': {e}")

    if not ref_found and artifact_positions:
        print(f"   ⚠️  No references found (tested {len(artifact_positions)} artifact positions)")

    print("\n✅ Testing complete!")

    # Summary
    print("\n📊 Summary:")
    print(f"   - Diagnostics: {'✅ Published' if captured_diagnostics else '⚠️  None'}")
    print(f"   - Hover: {'✅ Working' if hover_found else '⚠️  Not tested'}")
    print(f"   - Go-to-Definition: {'✅ Working' if def_found else '⚠️  Not tested'}")
    print(f"   - Find-References: {'✅ Working' if ref_found else '⚠️  Not tested'}")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_lsp_manual.py <manifest-file>")
        print("\nExample:")
        print("  python scripts/test_lsp_manual.py manifests/task-001-package-init.manifest.json")
        sys.exit(1)

    manifest_path = Path(sys.argv[1])
    if not manifest_path.exists():
        print(f"Error: File not found: {manifest_path}")
        sys.exit(1)

    asyncio.run(test_manifest(manifest_path))


if __name__ == "__main__":
    main()
