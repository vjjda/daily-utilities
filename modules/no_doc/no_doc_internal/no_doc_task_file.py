# Path: modules/no_doc/no_doc_internal/no_doc_task_file.py
"""
(Internal Task)
Handles the logic for processing a single, user-specified source file.
"""

import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

# SỬA: Đổi tên analyzer
from .no_doc_analyzer import analyze_file_for_cleaning_and_formatting

from ..no_doc_executor import print_dry_run_report_for_group

__all__ = ["process_no_doc_task_file"]

FileResult = Dict[str, Any]

def process_no_doc_task_file(
    file_path: Path,
    cli_args: argparse.Namespace,
    file_extensions: Set[str],
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path,
    # SỬA: Thêm tham số format
    format_flag: bool,
    format_extensions_set: Set[str]
) -> List[FileResult]:
    """
    Xử lý logic no_doc cho một file riêng lẻ.
    """
    logger.info(
        f"--- 📄 Đang xử lý file: {file_path.relative_to(reporting_root).as_posix()} ---"
    )

    file_only_results: List[FileResult] = []
    resolved_file = file_path.resolve()
    if resolved_file in processed_files:
        logger.info("   -> Bỏ qua (đã xử lý).")
        logger.info("")
        return []

    file_ext = "".join(file_path.suffixes) # Giữ dấu .
    if file_ext not in file_extensions:
        logger.warning(
            f"⚠️ Bỏ qua file '{file_path.name}': không khớp extensions ({file_ext})"
        )
        logger.info("")
        return []

    all_clean: bool = getattr(cli_args, "all_clean", False)
    
    # SỬA: Gọi analyzer mới
    result = analyze_file_for_cleaning_and_formatting(
        file_path=file_path, 
        logger=logger, 
        all_clean=all_clean,
        format_flag=format_flag,
        format_extensions_set=format_extensions_set
    )
    if result:
        file_only_results.append(result)
    processed_files.add(resolved_file)

    if file_only_results:
        print_dry_run_report_for_group(
            logger, file_path.name, file_only_results, reporting_root
        )
    else:
        logger.info(f"  -> ✅ File đã sạch / đã định dạng.") # SỬA: Cập nhật thông báo

    logger.info("")
    return file_only_results