# Path: modules/pack_code/pack_code_internal/pack_code_tree.py
from pathlib import Path
from typing import List, Dict, Any, Set

__all__ = ["generate_tree_string"]


def generate_tree_string(
    start_path: Path, file_paths: List[Path], scan_root: Path
) -> str:
    if not file_paths:
        return ""

    tree_lines: List[str] = []

    try:

        root_display = start_path.relative_to(scan_root).as_posix()
        if root_display == ".":

            root_display = scan_root.name
    except ValueError:

        root_display = start_path.name

    tree_lines.append(f"{root_display}{'/' if start_path.is_dir() else ''}")

    if not start_path.is_dir():
        return "\n".join(tree_lines)

    all_relative_parts: Set[Path] = set()
    for p in file_paths:
        try:
            rel_p = p.relative_to(start_path)
            all_relative_parts.add(rel_p)

            for parent in rel_p.parents:
                if parent != Path("."):
                    all_relative_parts.add(parent)
        except ValueError:

            continue

    if not all_relative_parts:
        return "\n".join(tree_lines)

    sorted_parts = sorted(list(all_relative_parts), key=lambda p: p.parts)

    level_prefixes: Dict[int, str] = {}

    for i, part in enumerate(sorted_parts):
        level = len(part.parts) - 1

        prefix = ""
        for l in range(level):
            prefix += level_prefixes.get(l, "    ")

        siblings = [
            p
            for p in sorted_parts
            if p.parent == part.parent and len(p.parts) == len(part.parts)
        ]
        is_last = part == siblings[-1]
        pointer = "└── " if is_last else "├── "

        is_directory = any(p.parent == part for p in sorted_parts)

        line = f"{prefix}{pointer}{part.name}{'/' if is_directory else ''}"
        tree_lines.append(line)

        if is_directory:

            level_prefixes[level] = "    " if is_last else "│   "
        elif is_last:

            keys_to_remove = [k for k in level_prefixes if k >= level]
            for k in keys_to_remove:
                del level_prefixes[k]

    return "\n".join(tree_lines)