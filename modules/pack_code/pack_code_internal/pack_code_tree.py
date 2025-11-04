# Path: modules/pack_code/pack_code_internal/pack_code_tree.py
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
import logging

__all__ = ["generate_tree_string"]

FileResult = Dict[str, Any]


logger = logging.getLogger(__name__)


def generate_tree_string(
    all_file_results: List[FileResult], reporting_root: Optional[Path]
) -> str:
    if not all_file_results:
        return ""

    tree_lines: List[str] = []

    all_relative_paths_str: Set[str] = {r["rel_path"] for r in all_file_results}

    if reporting_root is None:
        logger.warning(
            "Không thể tạo cây thư mục: Đang xử lý các đường dẫn tuyệt đối từ nhiều nguồn."
        )
        tree_lines.append("[Không thể tạo cây: Nhiều gốc báo cáo]")

        for rel_path_str in sorted(list(all_relative_paths_str)):
            tree_lines.append(f"{rel_path_str}")
        return "\n".join(tree_lines)

    root_display = reporting_root.name

    if root_display == "" and reporting_root.parent == reporting_root:
        root_display = "/"
    elif root_display == "":
        root_display = "."

    tree_lines.append(f"{root_display}/")

    all_relative_parts: Set[Path] = set()
    for rel_path_str in all_relative_paths_str:
        rel_p = Path(rel_path_str)
        all_relative_parts.add(rel_p)
        for parent in rel_p.parents:
            if parent != Path("."):
                all_relative_parts.add(parent)

    if not all_relative_parts:
        return "\n".join(tree_lines)

    sorted_parts = sorted(list(all_relative_parts), key=lambda p: p.parts)
    level_prefixes: Dict[int, str] = {}

    for i, part in enumerate(sorted_parts):
        level = len(part.parts) - 1
        prefix = "".join(
            level_prefixes.get(level_index, "    ") for level_index in range(level)
        )

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
