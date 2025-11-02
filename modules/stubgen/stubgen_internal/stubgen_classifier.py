# Path: modules/stubgen/stubgen_internal/stubgen_classifier.py
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from utils.logging_config import log_success

StubResult = Dict[str, Any]

__all__ = ["classify_and_report_stub_changes"]


def _split_header_and_content(file_content: str) -> Tuple[Optional[str], str]:
    if not file_content:
        return None, ""

    lines = file_content.splitlines()
    first_line = lines[0].strip()

    if first_line.startswith("# Path:"):
        header = lines[0]
        body = "\n".join(lines[1:])
        return header, body
    else:
        return None, file_content


def classify_and_report_stub_changes(
    logger: logging.Logger,
    group_name: str,
    group_raw_results: List[StubResult],
    scan_root: Path,
) -> Tuple[List[StubResult], List[StubResult], List[StubResult]]:
    files_to_create: List[StubResult] = []
    files_to_overwrite: List[StubResult] = []
    files_no_change: List[StubResult] = []

    for result in group_raw_results:
        stub_path: Path = result["stub_path"]
        new_content_body: str = result["content"]

        if not stub_path.exists():
            files_to_create.append(result)
        else:
            try:
                existing_full_content = stub_path.read_text(encoding="utf-8")
                existing_header, existing_content_body = _split_header_and_content(
                    existing_full_content
                )

                if existing_content_body.strip() == new_content_body.strip():
                    files_no_change.append(result)
                else:
                    result["existing_header"] = existing_header
                    files_to_overwrite.append(result)
            except Exception as e:
                logger.warning(
                    f"Không thể đọc/so sánh stub {stub_path.name}: {e}. Đánh dấu là OVERWRITE."
                )
                result["existing_header"] = None
                files_to_overwrite.append(result)

    def get_rel_path(path: Path) -> str:
        try:
            return path.relative_to(scan_root).as_posix()
        except ValueError:
            return str(path)

    total_changes = len(files_to_create) + len(files_to_overwrite)
    if not total_changes and not files_no_change:
        return [], [], []

    logger.info(
        f"\n   --- 📄 Nhóm: {group_name} ({len(group_raw_results)} gateway) ---"
    )

    if files_no_change:
        logger.info(f"     ✅ Files up-to-date ({len(files_no_change)}):")
        for r in files_no_change:
            logger.info(
                f"        -> OK: {get_rel_path(r['stub_path'])} ({r['symbols_count']} symbols)"
            )

    if files_to_create:
        logger.info(f"     📝 Files to create ({len(files_to_create)}):")
        for r in files_to_create:
            logger.info(
                f"        -> NEW: {get_rel_path(r['stub_path'])} ({r['symbols_count']} symbols)"
            )

    if files_to_overwrite:
        logger.warning(f"     ⚠️ Files to OVERWRITE ({len(files_to_overwrite)}):")
        for r in files_to_overwrite:
            logger.warning(
                f"        -> OVERWRITE: {get_rel_path(r['stub_path'])} ({r['symbols_count']} symbols)"
            )

    return files_to_create, files_to_overwrite, files_no_change
