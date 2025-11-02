# Path: modules/no_doc/no_doc_internal/no_doc_reporter.py
import logging
from pathlib import Path
from typing import List, Dict, Any
# --- THÊM IMPORT MỚI ---
from utils.cli.ui_helpers import print_grouped_report
# --- KẾT THÚC THÊM IMPORT ---

FileResult = Dict[str, Any]

__all__ = ["print_dry_run_report_for_group"]


def print_dry_run_report_for_group(
    logger: logging.Logger,
    group_name: str,
    files_in_group: List[FileResult],
    scan_root: Path,
) -> None:
    
    # --- Định nghĩa các hàm formatter cục bộ ---
    def _title_formatter(info: FileResult) -> str:
        file_path: Path = info["path"]
        try:
            rel_path = file_path.relative_to(scan_root).as_posix()
        except ValueError:
            rel_path = str(file_path)
        # Gộp thông báo vào tiêu đề
        return f"{rel_path} (Sẽ bị thay đổi định dạng do AST unparse)"

    def _detail_formatter(info: FileResult) -> List[str]:
        # ndoc không có chi tiết (đã gộp vào title)
        return []
    # --- Kết thúc formatter ---

    # --- Gọi hàm helper chung ---
    print_grouped_report(
        logger=logger,
        group_name=group_name,
        files_in_group=files_in_group,
        scan_root=scan_root,
        title_formatter=_title_formatter,
        detail_formatter=_detail_formatter,
    )
    # --- Kết thúc gọi helper ---