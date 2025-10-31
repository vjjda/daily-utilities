# Path: modules/check_path/check_path_internal/check_path_task_file.py
"""
(Internal Task)
Handles the logic for processing a single, user-specified source file.
"""

import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

# SỬA: Import trực tiếp từ các file worker
from .check_path_merger import merge_check_path_configs
from .check_path_analyzer import analyze_single_file_for_path_comment
# (Config import không cần thiết ở đây, nó đã được chuyển vào core)

# Import hàm báo cáo từ executor (public)
from ..check_path_executor import print_dry_run_report_for_group

__all__ = ["process_check_path_task_file"]

FileResult = Dict[str, Any] # Type alias

def process_check_path_task_file(
    file_path: Path,
    cli_args: argparse.Namespace,
    file_extensions: Set[str], # Set extensions đã merge
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path
) -> List[FileResult]:
    """
    Xử lý logic cpath cho một file riêng lẻ.
    """
    logger.info(f"--- 📄 Đang xử lý file: {file_path.relative_to(reporting_root).as_posix()} ---")
    
    file_only_results: List[FileResult] = []
    resolved_file = file_path.resolve()
    if resolved_file in processed_files:
        logger.info("   -> Bỏ qua (đã xử lý).")
        logger.info("")
        return []
        
    # 1. Kiểm tra extension
    file_ext = "".join(file_path.suffixes) # Giữ dấu .
    if file_ext not in file_extensions:
        logger.warning(
            f"⚠️ Bỏ qua file '{file_path.name}': không khớp extensions ({file_ext})"
        )
        logger.info("")
        return []

    # 2. Phân tích
    # Dùng thư mục cha làm scan_root
    scan_root = file_path.parent
    result = analyze_single_file_for_path_comment(file_path, scan_root, logger)
    if result:
        file_only_results.append(result)
    processed_files.add(resolved_file)
    
    # 3. Báo cáo
    if file_only_results:
        print_dry_run_report_for_group(logger, file_path.name, file_only_results, reporting_root)
    else:
        logger.info(f"  -> ✅ Path comment đã chính xác.")

    logger.info("") # Dòng trống
    return file_only_results