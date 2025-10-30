# Path: modules/pack_code/pack_code_internal/pack_code_builder.py
from pathlib import Path
from typing import Dict, Any, List, Optional

__all__ = ["assemble_packed_content"]


def assemble_packed_content(
    files_to_pack: List[Path],
    files_content: Dict[Path, str],
    scan_root: Path,
    tree_str: str,
    no_header: bool,
    dry_run: bool,
) -> str:

    final_content_lines: List[str] = []

    if tree_str:
        final_content_lines.append(tree_str)
        final_content_lines.append("\n" + ("=" * 80) + "\n")

    if not dry_run:
        for file_path in files_to_pack:
            content = files_content.get(file_path)
            if content is None:

                continue

            try:

                rel_path_str = file_path.relative_to(scan_root).as_posix()
            except ValueError:
                rel_path_str = file_path.as_posix()

            if not no_header:
                header = f"===== Path: {rel_path_str} ====="
                final_content_lines.append(header)

            final_content_lines.append(content)

            if not no_header:
                final_content_lines.append("\n")

    return "\n".join(final_content_lines)