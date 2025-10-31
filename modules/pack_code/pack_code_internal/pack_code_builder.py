# Path: modules/pack_code/pack_code_internal/pack_code_builder.py
from pathlib import Path
from typing import Dict, Any, List, Optional

__all__ = ["assemble_packed_content"]

FileResult = Dict[str, Any]


def assemble_packed_content(
    all_file_results: List[FileResult],
    tree_str: str,
    no_header: bool,
    dry_run: bool,
) -> str:
    final_content_lines: List[str] = []

    if tree_str:
        final_content_lines.append(tree_str)
        final_content_lines.append("\n" + ("=" * 80) + "\n")

    if not dry_run:

        sorted_results = sorted(all_file_results, key=lambda r: r["rel_path"])

        for result in sorted_results:
            content = result.get("content")
            if content is None:
                continue

            rel_path_str = result["rel_path"]

            if not no_header:
                header = f"===== Path: {rel_path_str} ====="
                final_content_lines.append(header)

            final_content_lines.append(content)

            if not no_header:
                final_content_lines.append("\n")

    return "\n".join(final_content_lines)