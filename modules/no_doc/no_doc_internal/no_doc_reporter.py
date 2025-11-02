# Path: modules/no_doc/no_doc_internal/no_doc_reporter.py
import logging
from pathlib import Path
from typing import List, Dict, Any

FileResult = Dict[str, Any]

__all__ = ["print_dry_run_report_for_group"]


def print_dry_run_report_for_group(
    logger: logging.Logger,
    group_name: str,
    files_in_group: List[FileResult],
    scan_root: Path,
) -> None:
    logger.warning(f"\n   --- Nhóm: {group_name} ({len(files_in_group)} file) ---")
    for info in files_in_group:
        file_path: Path = info["path"]
        try:
            rel_path = file_path.relative_to(scan_root).as_posix()
        except ValueError:
            rel_path = str(file_path)

        logger.warning(f"   -> {rel_path} (Sẽ bị thay đổi định dạng do AST unparse)")
