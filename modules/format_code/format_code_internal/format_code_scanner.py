# Path: modules/format_code/format_code_internal/format_code_scanner.py

import logging
from pathlib import Path
import sys
from typing import List, Set, Optional, TYPE_CHECKING, Iterable, Tuple, Dict


if not "PROJECT_ROOT" in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

try:
    import pathspec
except ImportError:
    pathspec = None

if TYPE_CHECKING:
    import pathspec

from utils.core import (
    get_submodule_paths,
    parse_gitignore,
    is_path_matched,
    compile_spec_from_patterns,
)

__all__ = ["scan_files"]


def scan_files(
    logger: logging.Logger,
    start_path: Path,
    ignore_list: List[str],
    extensions: List[str],
    scan_root: Path,
    script_file_path: Path,
) -> Tuple[List[Path], Dict[str, bool]]:
    scan_status = {"gitignore_found": False, "gitmodules_found": False}

    scan_path = start_path.resolve()

    if not scan_path.exists():
        logger.warning(f"Thư mục quét không tồn tại: {scan_path.as_posix()}")
        return [], scan_status

    submodule_paths = get_submodule_paths(scan_root, logger)
    if submodule_paths:
        scan_status["gitmodules_found"] = True

    gitignore_patterns: List[str] = parse_gitignore(scan_root)
    if gitignore_patterns:
        scan_status["gitignore_found"] = True

    all_ignore_patterns_list: List[str] = ignore_list + gitignore_patterns
    ignore_spec = compile_spec_from_patterns(all_ignore_patterns_list, scan_root)

    all_files: List[Path] = []

    if scan_path.is_dir():
        for ext in extensions:
            all_files.extend(scan_path.rglob(f"*.{ext}"))
    elif scan_path.is_file():
        file_ext = "".join(scan_path.suffixes).lstrip(".")
        if file_ext in extensions:
            all_files.append(scan_path)
        else:
            logger.warning(
                f"File '{scan_path.name}' bị bỏ qua do không khớp extension: {file_ext}"
            )
            return [], scan_status

    files_to_process: List[Path] = []

    for file_path in all_files:
        abs_file_path = file_path.resolve()

        if abs_file_path.samefile(script_file_path.resolve()):
            continue

        is_in_submodule = any(abs_file_path.is_relative_to(p) for p in submodule_paths)
        if is_in_submodule:
            continue

        if is_path_matched(file_path, ignore_spec, scan_root):
            continue

        files_to_process.append(file_path)

    files_to_process.sort(key=lambda p: p.as_posix())
    return files_to_process, scan_status